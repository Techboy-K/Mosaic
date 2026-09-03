-- ============================================================================
-- 009 — Storage for dish photos and staff avatars.
-- Buckets are size- and MIME-capped at the platform level; RLS decides who may
-- write. The client also checks magic bytes, but that is convenience — this is
-- the boundary that actually holds.
-- ============================================================================

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('menu-images','menu-images', true,  5242880,
   array['image/jpeg','image/png','image/webp']),
  ('avatars','avatars',         true,  2097152,
   array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types,
      public = excluded.public;

-- anyone may read (the public site shows dish photos); writes are gated
create policy "menu images are readable"
  on storage.objects for select using (bucket_id = 'menu-images');
create policy "menu images writable with menu.edit"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'menu-images' and has_perm('menu.edit'));
create policy "menu images updatable with menu.edit"
  on storage.objects for update to authenticated
  using (bucket_id = 'menu-images' and has_perm('menu.edit'));
create policy "menu images deletable with menu.edit"
  on storage.objects for delete to authenticated
  using (bucket_id = 'menu-images' and has_perm('menu.edit'));

create policy "avatars are readable"
  on storage.objects for select using (bucket_id = 'avatars');
-- you may write your own avatar; changing someone else's needs users.edit
create policy "avatars writable"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars'
    and (owner = auth.uid() or has_perm('users.edit')));
create policy "avatars updatable"
  on storage.objects for update to authenticated
  using (bucket_id = 'avatars'
    and (owner = auth.uid() or has_perm('users.edit')));
create policy "avatars deletable"
  on storage.objects for delete to authenticated
  using (bucket_id = 'avatars'
    and (owner = auth.uid() or has_perm('users.edit')));
