-- ============================================================================
-- Mosaic crew portal — 001 RBAC foundation
-- Authorization lives in the database. Every policy resolves through has_perm()
-- so a forged client cannot widen its own access.
-- ============================================================================

create extension if not exists "pgcrypto";

-- ─────────────────────────────────────────────── restaurants
create table restaurants (
  id          uuid primary key default gen_random_uuid(),
  slug        text unique not null,
  name        text not null,
  address     text,
  phone       text,
  timezone    text not null default 'Asia/Dubai',
  is_active   boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- ─────────────────────────────────────────────── permissions (resource.action)
create table permissions (
  id          uuid primary key default gen_random_uuid(),
  key         text unique not null,          -- 'orders.view'
  resource    text not null,                 -- 'orders'
  action      text not null,                 -- 'view'
  description text,
  created_at  timestamptz not null default now(),
  constraint permissions_key_shape check (key = resource || '.' || action)
);

-- ─────────────────────────────────────────────── roles
-- hierarchy_level: lower number = more authority. Superadmin is 0.
create table roles (
  id              uuid primary key default gen_random_uuid(),
  key             text unique not null,
  name            text not null,
  description     text,
  icon            text,
  color           text,
  hierarchy_level int not null,
  is_system       boolean not null default false,   -- shipped with the product
  is_active       boolean not null default true,
  created_by      uuid,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  constraint roles_level_nonneg check (hierarchy_level >= 0)
);
create index roles_level_idx on roles(hierarchy_level);

create table role_permissions (
  role_id       uuid not null references roles(id) on delete cascade,
  permission_id uuid not null references permissions(id) on delete cascade,
  granted_at    timestamptz not null default now(),
  primary key (role_id, permission_id)
);

-- pages a role may open; navigation is derived from this, never hardcoded
create table role_pages (
  role_id uuid not null references roles(id) on delete cascade,
  page_key text not null,
  sort_order int not null default 0,
  primary key (role_id, page_key)
);

-- ─────────────────────────────────────────────── profiles (extends auth.users)
-- Credentials stay in auth.users. We never store a password.
create table profiles (
  id               uuid primary key references auth.users(id) on delete cascade,
  email            text not null,
  full_name        text not null default '',
  avatar_path      text,
  phone            text,
  is_active        boolean not null default true,
  is_system_owner  boolean not null default false,  -- permanently protected, see trigger
  last_login_at    timestamptz,
  created_by       uuid references profiles(id),
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index profiles_active_idx on profiles(is_active);

create table user_roles (
  user_id     uuid not null references profiles(id) on delete cascade,
  role_id     uuid not null references roles(id) on delete restrict,
  assigned_by uuid references profiles(id),
  assigned_at timestamptz not null default now(),
  primary key (user_id, role_id)
);

create table user_restaurants (
  user_id       uuid not null references profiles(id) on delete cascade,
  restaurant_id uuid not null references restaurants(id) on delete cascade,
  assigned_at   timestamptz not null default now(),
  primary key (user_id, restaurant_id)
);

-- ─────────────────────────────────────────────── audit (append-only)
create table audit_logs (
  id            bigserial primary key,
  actor_id      uuid references profiles(id),
  actor_email   text,
  actor_role    text,
  action        text not null,
  resource      text not null,
  resource_id   text,
  restaurant_id uuid references restaurants(id),
  before        jsonb,
  after         jsonb,
  ip            inet,
  created_at    timestamptz not null default now()
);
create index audit_created_idx  on audit_logs(created_at desc);
create index audit_actor_idx    on audit_logs(actor_id);
create index audit_resource_idx on audit_logs(resource, resource_id);

create table login_attempts (
  id         bigserial primary key,
  email      text not null,
  ip         inet,
  succeeded  boolean not null,
  created_at timestamptz not null default now()
);
create index login_attempts_idx on login_attempts(email, created_at desc);

-- ============================================================================
-- Authorization helpers. SECURITY DEFINER + a pinned search_path so callers
-- cannot shadow the tables these read.
-- ============================================================================

create or replace function auth_level()
returns int language sql stable security definer set search_path = public as $$
  select coalesce(min(r.hierarchy_level), 9999)
  from user_roles ur
  join roles r on r.id = ur.role_id and r.is_active
  join profiles p on p.id = ur.user_id and p.is_active
  where ur.user_id = auth.uid();
$$;

create or replace function has_perm(perm text)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1
    from user_roles ur
    join roles r            on r.id  = ur.role_id and r.is_active
    join role_permissions rp on rp.role_id = r.id
    join permissions pm      on pm.id = rp.permission_id
    join profiles pf         on pf.id = ur.user_id and pf.is_active
    where ur.user_id = auth.uid() and pm.key = perm
  );
$$;

create or replace function is_superadmin()
returns boolean language sql stable security definer set search_path = public as $$
  select auth_level() = 0;
$$;

create or replace function can_access_restaurant(rid uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select is_superadmin()
      or exists (select 1 from user_restaurants
                 where user_id = auth.uid() and restaurant_id = rid);
$$;

-- true when the caller outranks the target user (strictly)
create or replace function outranks(target uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select auth_level() < coalesce((
    select min(r.hierarchy_level) from user_roles ur
    join roles r on r.id = ur.role_id
    where ur.user_id = target
  ), 9999);
$$;

-- ============================================================================
-- System-owner protection. Enforced in the database, not the UI.
-- ============================================================================

create or replace function protect_system_owner()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'DELETE' then
    if old.is_system_owner then
      raise exception 'The system owner account cannot be deleted.' using errcode = '42501';
    end if;
    return old;
  end if;

  if old.is_system_owner then
    if new.is_active = false then
      raise exception 'The system owner account cannot be disabled.' using errcode = '42501';
    end if;
    if new.is_system_owner = false then
      raise exception 'System owner status cannot be removed.' using errcode = '42501';
    end if;
  end if;

  -- only an existing system owner may mint another one
  if new.is_system_owner and not coalesce(old.is_system_owner, false) then
    if not exists (select 1 from profiles
                   where id = auth.uid() and is_system_owner) then
      raise exception 'Only a system owner can grant system owner status.' using errcode = '42501';
    end if;
  end if;
  return new;
end $$;

create trigger trg_protect_system_owner
  before update or delete on profiles
  for each row execute function protect_system_owner();

-- the owner's superadmin role cannot be stripped
create or replace function protect_owner_roles()
returns trigger language plpgsql security definer set search_path = public as $$
declare owner boolean;
begin
  select is_system_owner into owner from profiles where id = old.user_id;
  if owner then
    raise exception 'Roles cannot be removed from the system owner.' using errcode = '42501';
  end if;
  return old;
end $$;

create trigger trg_protect_owner_roles
  before delete on user_roles
  for each row execute function protect_owner_roles();

-- ============================================================================
-- Privilege-escalation guard: nobody may grant a role at or above their own
-- authority, and nobody may act on a user who outranks them.
-- ============================================================================

create or replace function guard_role_assignment()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  actor_level  int;
  target_level int;
begin
  -- seeding runs as service_role, which has no auth.uid()
  if auth.uid() is null then return new; end if;

  actor_level  := auth_level();
  select hierarchy_level into target_level from roles where id = new.role_id;

  if not has_perm('users.assign_role') then
    raise exception 'You do not have permission to assign roles.' using errcode = '42501';
  end if;

  if target_level <= actor_level then
    raise exception
      'You cannot assign a role at or above your own authority (yours %, target %).',
      actor_level, target_level using errcode = '42501';
  end if;

  if not outranks(new.user_id) and new.user_id <> auth.uid() then
    raise exception 'You cannot modify a user at or above your own authority.' using errcode = '42501';
  end if;

  return new;
end $$;

create trigger trg_guard_role_assignment
  before insert or update on user_roles
  for each row execute function guard_role_assignment();

-- ============================================================================
-- updated_at
-- ============================================================================
create or replace function touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at := now(); return new; end $$;

create trigger trg_touch_restaurants before update on restaurants
  for each row execute function touch_updated_at();
create trigger trg_touch_roles before update on roles
  for each row execute function touch_updated_at();
create trigger trg_touch_profiles before update on profiles
  for each row execute function touch_updated_at();
