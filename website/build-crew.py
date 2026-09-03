# -*- coding: utf-8 -*-
"""Generate the /crew pages from one shell, the same way the public site is built."""
import os
W = os.path.dirname(os.path.abspath(__file__))

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#141928">
<link rel="icon" href="../assets/img/brand/logo.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=PT+Sans:wght@400;700&family=Poppins:wght@300;400;500;600&display=swap">
<link rel="stylesheet" href="../assets/css/site.css">
<link rel="stylesheet" href="../assets/css/crew.css">
{extra_css}</head>
<body class="crew{body_class}">
"""

TAIL = """<script src="../assets/js/vendor/supabase.min.js"></script>
<script src="../assets/js/crew/config.js"></script>
<script src="../assets/js/crew/auth.js"></script>
<script src="../assets/js/crew/shell.js"></script>
{scripts}</body>
</html>
"""

def page(fname, title, body, scripts='', extra_css='', body_class=''):
    html = (HEAD.format(title=title, extra_css=extra_css, body_class=body_class)
            + body + TAIL.format(scripts=scripts))
    open(os.path.join(W, 'crew', fname), 'w', encoding='utf-8').write(html)
    return fname

def shell_page(fname, title, page_key, inner, scripts=''):
    """A page inside the authenticated chrome."""
    body = '<div id="crew-shell"></div>\n<main id="crew-main" hidden>\n' + inner + '\n</main>\n'
    boot = ('<script>(async function(){'
            'var c = await Crew.requirePage(' + (("'"+page_key+"'") if page_key else 'null') + ');'
            'if(!c) return;'
            'CrewShell.render(c);'
            'if (window.CrewNotify) CrewNotify.mount(c);'
            'document.getElementById("crew-main").hidden = false;'
            'if (window.pageInit) window.pageInit(c);'
            '})();</script>')
    return page(fname, title, body, scripts + boot)
