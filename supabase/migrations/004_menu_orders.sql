-- ============================================================================
-- 004 — Menu CMS, orders, the state machine, notifications.
-- Order status can only ever change through transition_order(); the column is
-- locked by a trigger so no client can write it directly.
-- ============================================================================

-- ─────────────────────────────────────────────── menu
create table menu_categories (
  id            uuid primary key default gen_random_uuid(),
  restaurant_id uuid references restaurants(id) on delete cascade,   -- null = shared
  slug          text not null,
  name          text not null,
  sort_order    int  not null default 0,
  is_active     boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  unique (restaurant_id, slug)
);

create table menu_items (
  id            uuid primary key default gen_random_uuid(),
  category_id   uuid not null references menu_categories(id) on delete cascade,
  restaurant_id uuid references restaurants(id) on delete cascade,
  external_id   int,                       -- their WooCommerce product id
  name          text not null,
  description   text,
  price         numeric(10,2) not null default 0,
  currency      char(3) not null default 'AED',
  image_path    text,
  is_available  boolean not null default true,
  dietary       text[] not null default '{}',
  allergens     text[] not null default '{}',
  sort_order    int not null default 0,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index menu_items_cat_idx on menu_items(category_id, sort_order);
create index menu_items_ext_idx on menu_items(external_id);

create table menu_item_modifiers (
  id           uuid primary key default gen_random_uuid(),
  item_id      uuid not null references menu_items(id) on delete cascade,
  name         text not null,
  price_delta  numeric(10,2) not null default 0,
  sort_order   int not null default 0
);

-- ─────────────────────────────────────────────── order status catalogue
-- Configurable rather than a hardcoded enum, so states can be added later.
create table order_status_defs (
  key            text primary key,
  label          text not null,
  owner_role_key text,                  -- whose queue the order sits in
  sort_order     int not null,
  is_terminal    boolean not null default false,
  colour         text
);
insert into order_status_defs (key,label,owner_role_key,sort_order,is_terminal,colour) values
  ('DRAFT','Draft','waiter',10,false,'#7A7F8C'),
  ('SUBMITTED','Submitted','waiter',20,false,'#39497C'),
  ('SENT_TO_KITCHEN','Sent to kitchen','chef',30,false,'#8E6238'),
  ('IN_PREPARATION','In preparation','chef',40,false,'#B4761B'),
  ('READY','Ready','waiter',50,false,'#2F6F4F'),
  ('SERVED','Served','waiter',60,false,'#4C6B5A'),
  ('COMPLETED','Completed',null,70,true,'#5A6070'),
  ('CANCELLED','Cancelled',null,80,true,'#B3261E'),
  ('NEEDS_ATTENTION','Needs attention','supervisor',90,false,'#B3261E');

create table order_transitions (
  from_status text not null references order_status_defs(key),
  to_status   text not null references order_status_defs(key),
  primary key (from_status, to_status)
);
insert into order_transitions (from_status,to_status) values
  ('DRAFT','SUBMITTED'),('DRAFT','CANCELLED'),
  ('SUBMITTED','SENT_TO_KITCHEN'),('SUBMITTED','DRAFT'),('SUBMITTED','CANCELLED'),
  ('SENT_TO_KITCHEN','IN_PREPARATION'),('SENT_TO_KITCHEN','SUBMITTED'),
  ('SENT_TO_KITCHEN','CANCELLED'),('SENT_TO_KITCHEN','NEEDS_ATTENTION'),
  ('IN_PREPARATION','READY'),('IN_PREPARATION','SENT_TO_KITCHEN'),
  ('IN_PREPARATION','NEEDS_ATTENTION'),('IN_PREPARATION','CANCELLED'),
  ('READY','SERVED'),('READY','IN_PREPARATION'),('READY','NEEDS_ATTENTION'),
  ('SERVED','COMPLETED'),('SERVED','READY'),
  ('NEEDS_ATTENTION','SENT_TO_KITCHEN'),('NEEDS_ATTENTION','IN_PREPARATION'),
  ('NEEDS_ATTENTION','READY'),('NEEDS_ATTENTION','CANCELLED');

-- ─────────────────────────────────────────────── orders
create sequence order_number_seq start 1000;

create table orders (
  id             uuid primary key default gen_random_uuid(),
  number         int not null default nextval('order_number_seq'),
  restaurant_id  uuid not null references restaurants(id) on delete restrict,
  status         text not null default 'DRAFT' references order_status_defs(key),
  priority       text not null default 'NORMAL' check (priority in ('NORMAL','HIGH','URGENT')),
  table_label    text,
  created_by     uuid references profiles(id),
  owner_id       uuid references profiles(id),      -- whose queue it is in right now
  notes          text,
  is_quick_note  boolean not null default false,    -- fallback capture
  quick_note_text text,
  submitted_at   timestamptz,
  ready_at       timestamptz,
  served_at      timestamptz,
  completed_at   timestamptz,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index orders_rest_status_idx on orders(restaurant_id, status);
create index orders_owner_idx       on orders(owner_id);
create index orders_created_idx     on orders(created_at desc);
create unique index orders_number_idx on orders(number);

create table order_items (
  id          uuid primary key default gen_random_uuid(),
  order_id    uuid not null references orders(id) on delete cascade,
  item_id     uuid references menu_items(id) on delete set null,
  name        text not null,           -- captured, so history survives menu edits
  unit_price  numeric(10,2) not null default 0,
  qty         int not null default 1 check (qty > 0),
  notes       text,
  created_at  timestamptz not null default now()
);
create index order_items_order_idx on order_items(order_id);

-- immutable trail. Also carries the server-owned undo window.
create table order_events (
  id              bigserial primary key,
  order_id        uuid not null references orders(id) on delete cascade,
  actor_id        uuid references profiles(id),
  actor_role      text,
  action          text not null,
  from_status     text,
  to_status       text,
  from_owner      uuid references profiles(id),
  to_owner        uuid references profiles(id),
  metadata        jsonb,
  undo_expires_at timestamptz,          -- non-null while the handoff is reversible
  undone_at       timestamptz,
  created_at      timestamptz not null default now()
);
create index order_events_order_idx on order_events(order_id, created_at);

create table notifications (
  id          bigserial primary key,
  user_id     uuid references profiles(id) on delete cascade,
  role_key    text,                     -- broadcast to a whole role instead
  restaurant_id uuid references restaurants(id) on delete cascade,
  kind        text not null,
  title       text not null,
  body        text,
  order_id    uuid references orders(id) on delete cascade,
  read_at     timestamptz,
  created_at  timestamptz not null default now()
);
create index notif_user_idx on notifications(user_id, read_at, created_at desc);
create index notif_role_idx on notifications(role_key, restaurant_id, created_at desc);

create trigger trg_touch_menu_cat before update on menu_categories
  for each row execute function touch_updated_at();
create trigger trg_touch_menu_item before update on menu_items
  for each row execute function touch_updated_at();
create trigger trg_touch_orders before update on orders
  for each row execute function touch_updated_at();

-- ============================================================================
-- The status column is not writable directly. Only transition_order() may
-- change it, which it signals with a transaction-local flag.
-- ============================================================================
create or replace function guard_order_status()
returns trigger language plpgsql as $$
begin
  if new.status is distinct from old.status
     and coalesce(current_setting('mosaic.in_transition', true), '') <> '1' then
    raise exception
      'Order status may only change through transition_order().' using errcode = '42501';
  end if;
  return new;
end $$;

create trigger trg_guard_order_status
  before update on orders
  for each row execute function guard_order_status();
