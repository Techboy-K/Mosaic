/* Secure image upload.
   Storage RLS and the bucket's own MIME/size caps are the real boundary; these
   checks exist so a mistake is caught before the round trip, and so a file that
   merely *claims* to be a JPEG is rejected. */
(function (w) {
  'use strict';

  var SIGS = [
    { mime:'image/jpeg', ext:'jpg',  bytes:[0xFF,0xD8,0xFF] },
    { mime:'image/png',  ext:'png',  bytes:[0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A] },
    { mime:'image/webp', ext:'webp', bytes:[0x52,0x49,0x46,0x46], at8:[0x57,0x45,0x42,0x50] }
  ];

  /* Read the leading bytes and compare against real signatures. An .exe renamed
     to .jpg fails here; so does an SVG, which can carry script. */
  function sniff(file) {
    return new Promise(function (resolve) {
      var r = new FileReader();
      r.onload = function () {
        var b = new Uint8Array(r.result);
        for (var i = 0; i < SIGS.length; i++) {
          var s = SIGS[i], ok = s.bytes.every(function (v, j) { return b[j] === v; });
          if (ok && s.at8) ok = s.at8.every(function (v, j) { return b[8 + j] === v; });
          if (ok) return resolve(s);
        }
        resolve(null);
      };
      r.onerror = function () { resolve(null); };
      r.readAsArrayBuffer(file.slice(0, 16));
    });
  }

  function dimensions(file) {
    return new Promise(function (resolve) {
      var img = new Image(), url = URL.createObjectURL(file);
      img.onload = function () { URL.revokeObjectURL(url); resolve({ w: img.width, h: img.height }); };
      img.onerror = function () { URL.revokeObjectURL(url); resolve(null); };
      img.src = url;
    });
  }

  /* Downscale in the browser so we never ship a 12MP phone photo to a kitchen tablet. */
  function shrink(file, maxPx, quality) {
    return new Promise(function (resolve) {
      var img = new Image(), url = URL.createObjectURL(file);
      img.onload = function () {
        URL.revokeObjectURL(url);
        var scale = Math.min(1, maxPx / Math.max(img.width, img.height));
        if (scale === 1 && file.size < 400000) return resolve(file);
        var c = document.createElement('canvas');
        c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        c.toBlob(function (b) { resolve(b || file); }, 'image/webp', quality || 0.85);
      };
      img.onerror = function () { URL.revokeObjectURL(url); resolve(file); };
      img.src = url;
    });
  }

  /* The stored name is generated, never taken from the user — no path traversal,
     no unicode tricks, no collisions. */
  function safeName(ext) {
    var a = new Uint8Array(16); crypto.getRandomValues(a);
    return Array.from(a).map(function (n) { return n.toString(16).padStart(2,'0'); }).join('') + '.' + ext;
  }

  w.CrewUpload = {
    /* bucket: 'menu-images' | 'avatars' */
    async image(file, bucket, opts) {
      opts = opts || {};
      var maxBytes = opts.maxBytes || (bucket === 'avatars' ? 2097152 : 5242880);

      if (!file) return { error: 'No file chosen.' };
      if (file.size > maxBytes * 4)
        return { error: 'That file is far too large (' + Math.round(file.size/1048576) + ' MB).' };

      var sig = await sniff(file);
      if (!sig) return { error: 'That is not a JPEG, PNG or WebP image.' };

      var dim = await dimensions(file);
      if (!dim) return { error: 'That image could not be read.' };
      if (dim.w < 80 || dim.h < 80) return { error: 'Too small — at least 80×80 pixels.' };
      if (dim.w > 12000 || dim.h > 12000) return { error: 'Image dimensions are implausible.' };

      var blob = await shrink(file, opts.maxPx || (bucket === 'avatars' ? 512 : 1400),
                              opts.quality || 0.85);
      if (blob.size > maxBytes)
        return { error: 'Still ' + Math.round(blob.size/1048576) + ' MB after compression. Try a smaller image.' };

      var path = (opts.prefix ? opts.prefix.replace(/[^a-z0-9/_-]/gi,'') + '/' : '') +
                 safeName(blob.type === 'image/webp' ? 'webp' : sig.ext);

      var up = await Crew.sb.storage.from(bucket).upload(path, blob, {
        contentType: blob.type || sig.mime, cacheControl: '3600', upsert: false
      });
      if (up.error) return { error: up.error.message };

      var pub = Crew.sb.storage.from(bucket).getPublicUrl(path);
      return { path: path, url: pub.data.publicUrl, size: blob.size,
               width: dim.w, height: dim.h };
    },

    async remove(bucket, path) {
      if (!path) return;
      return Crew.sb.storage.from(bucket).remove([path]);
    }
  };
})(window);
