-- ============================================================================
-- 002 — Row Level Security.
-- Nothing is readable or writable except through these policies. The anon key
-- in the browser is therefore safe: it grants no access on its own.
-- ============================================================================

alter table restaurants      enable row level security;
alter table permissions      enable row level security;
alter table roles            enable row level security;
alter table role_permissions enable row level security;
alter table role_pages       enable row level security;
alter table profiles         enable row level security;
alter table user_roles       enable row level security;
alter table user_restaurants enable row level security;
alter table audit_logs       enable row level security;
alter table login_attempts   enable row level security;

-- ─────────────────────────────────────────────── restaurants
create policy restaurants_read on restaurants for select
  using (is_superadmin() or can_access_restaurant(id));
create policy restaurants_write on restaurants for update
  using (has_perm('restaurants.edit') and can_access_restaurant(id))
  with check (has_perm('restaurants.edit') and can_access_restaurant(id));
create policy restaurants_create on restaurants for insert
  with check (is_superadmin());
create policy restaurants_delete on restaurants for delete
  using (is_superadmin());

-- ─────────────────────────────────────────────── permissions (read-only catalogue)
create policy permissions_read on permissions for select
  using (auth.uid() is not null);

-- ─────────────────────────────────────────────── roles
-- Everyone signed in can read the catalogue; only roles.* permissions mutate it,
-- and nobody may create a role at or above their own authority.
create policy roles_read on roles for select
  using (auth.uid() is not null);
create policy roles_create on roles for insert
  with check (has_perm('roles.create') and hierarchy_level > auth_level());
create policy roles_update on roles for update
  using (has_perm('roles.edit') and hierarchy_level > auth_level() and not is_system)
  with check (has_perm('roles.edit') and hierarchy_level > auth_level());
create policy roles_delete on roles for delete
  using (has_perm('roles.delete') and hierarchy_level > auth_level() and not is_system);

create policy role_perms_read on role_permissions for select
  using (auth.uid() is not null);
create policy role_perms_write on role_permissions for all
  using (has_perm('roles.edit')
         and exists (select 1 from roles r where r.id = role_id
                     and r.hierarchy_level > auth_level() and not r.is_system))
  with check (has_perm('roles.edit')
         and exists (select 1 from roles r where r.id = role_id
                     and r.hierarchy_level > auth_level()));

create policy role_pages_read on role_pages for select
  using (auth.uid() is not null);
create policy role_pages_write on role_pages for all
  using (has_perm('roles.edit')
         and exists (select 1 from roles r where r.id = role_id
                     and r.hierarchy_level > auth_level() and not r.is_system))
  with check (has_perm('roles.edit')
         and exists (select 1 from roles r where r.id = role_id
                     and r.hierarchy_level > auth_level()));

-- ─────────────────────────────────────────────── profiles
create policy profiles_read_self on profiles for select
  using (id = auth.uid());
create policy profiles_read_others on profiles for select
  using (has_perm('users.view'));
create policy profiles_update_self on profiles for update
  using (id = auth.uid())
  with check (id = auth.uid());
-- editing someone else needs the permission AND strictly more authority
create policy profiles_update_others on profiles for update
  using (has_perm('users.edit') and outranks(id))
  with check (has_perm('users.edit') and outranks(id));
create policy profiles_insert on profiles for insert
  with check (has_perm('users.create'));
create policy profiles_delete on profiles for delete
  using (has_perm('users.delete') and outranks(id) and not is_system_owner);

-- ─────────────────────────────────────────────── user_roles
create policy user_roles_read on user_roles for select
  using (user_id = auth.uid() or has_perm('users.view'));
create policy user_roles_write on user_roles for insert
  with check (has_perm('users.assign_role'));   -- trigger does the hierarchy maths
create policy user_roles_update on user_roles for update
  using (has_perm('users.assign_role') and outranks(user_id))
  with check (has_perm('users.assign_role'));
create policy user_roles_delete on user_roles for delete
  using (has_perm('users.assign_role') and outranks(user_id));

-- ─────────────────────────────────────────────── user_restaurants
create policy user_rest_read on user_restaurants for select
  using (user_id = auth.uid() or has_perm('users.view'));
create policy user_rest_write on user_restaurants for all
  using (has_perm('users.edit') and outranks(user_id))
  with check (has_perm('users.edit') and outranks(user_id));

-- ─────────────────────────────────────────────── audit log: append-only
create policy audit_read on audit_logs for select
  using (has_perm('audit.view'));
create policy audit_insert on audit_logs for insert
  with check (auth.uid() is not null);
-- deliberately no update/delete policy: the log cannot be rewritten by anyone,
-- superadmin included. Belt and braces, revoke the grants too.
revoke update, delete on audit_logs from authenticated, anon;

create policy login_attempts_read on login_attempts for select
  using (has_perm('audit.view'));
