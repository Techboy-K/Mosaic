-- ============================================================================
-- 011 — Table bookings. The public site collects them; the crew portal works them.
-- ============================================================================

create table bookings (
  id             uuid primary key default gen_random_uuid(),
  reference      text unique not null default upper(substr(encode(gen_random_bytes(4),'hex'),1,6)),
  restaurant_id  uuid not null references restaurants(id) on delete restrict,
  guest_name     text not null,
  guest_phone    text not null,
  guest_email    text,
  party_size     int  not null check (party_size > 0),
  booking_date   date not null,
  booking_time   time not null,
  booking_type   text not null default 'Family'
                 check (booking_type in ('Business','Family','Friends')),
  notes          text,
  status         text not null default 'PENDING'
                 check (status in ('PENDING','CONFIRMED','SEATED','COMPLETED','NO_SHOW','CANCELLED')),
  preorder_order_id uuid references orders(id) on delete set null,
  source         text not null default 'website',
  handled_by     uuid references profiles(id),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index bookings_when_idx on bookings(restaurant_id, booking_date, booking_time);
create index bookings_status_idx on bookings(status, booking_date);

create trigger trg_touch_bookings before update on bookings
  for each row execute function touch_updated_at();

-- audit every status change without trusting the client to report it
create or replace function log_booking_change()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op='UPDATE' and new.status is distinct from old.status then
    insert into audit_logs (actor_id, actor_email, action, resource, resource_id, before, after)
    values (auth.uid(),
            (select email from profiles where id = auth.uid()),
            'booking.status', 'bookings', new.id::text,
            jsonb_build_object('status', old.status),
            jsonb_build_object('status', new.status));
  end if;
  return new;
end $$;
create trigger trg_log_booking after update on bookings
  for each row execute function log_booking_change();

insert into permissions (key, resource, action, description) values
  ('bookings.view','bookings','view','See table bookings'),
  ('bookings.manage','bookings','manage','Confirm, seat and cancel bookings')
on conflict (key) do nothing;

-- superadmin, admin and supervisor work the book
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p
where r.key in ('superadmin','admin','supervisor')
  and p.key in ('bookings.view','bookings.manage')
on conflict do nothing;

insert into role_pages (role_id, page_key, sort_order)
select r.id, 'bookings', 15 from roles r
where r.key in ('superadmin','admin','supervisor')
on conflict do nothing;

alter table bookings enable row level security;

create policy bookings_read on bookings for select
  using (has_perm('bookings.view') and can_access_restaurant(restaurant_id));
create policy bookings_update on bookings for update
  using (has_perm('bookings.manage') and can_access_restaurant(restaurant_id))
  with check (has_perm('bookings.manage') and can_access_restaurant(restaurant_id));
create policy bookings_insert_staff on bookings for insert to authenticated
  with check (has_perm('bookings.manage') and can_access_restaurant(restaurant_id));

-- The public booking form has no session. Rather than opening the table to
-- anon, it posts through this function: it can only ever INSERT a pending
-- booking, and cannot read anything back.
create or replace function public_create_booking(
  p_restaurant uuid, p_name text, p_phone text, p_email text,
  p_party int, p_date date, p_time time, p_type text, p_notes text)
returns text language plpgsql security definer set search_path = public as $$
declare ref text;
begin
  if length(coalesce(p_name,'')) < 2  then raise exception 'A name is required.'; end if;
  if length(coalesce(p_phone,'')) < 7 then raise exception 'A phone number is required.'; end if;
  if p_party is null or p_party < 1 or p_party > 60 then raise exception 'Party size looks wrong.'; end if;
  if p_date < current_date then raise exception 'That date has passed.'; end if;
  if p_type not in ('Business','Family','Friends') then p_type := 'Family'; end if;
  if not exists (select 1 from restaurants where id = p_restaurant and is_active) then
    raise exception 'Unknown restaurant.';
  end if;

  insert into bookings (restaurant_id, guest_name, guest_phone, guest_email,
                        party_size, booking_date, booking_time, booking_type, notes)
  values (p_restaurant, left(p_name,120), left(p_phone,40), left(p_email,160),
          p_party, p_date, p_time, p_type, left(p_notes,600))
  returning reference into ref;

  insert into notifications (role_key, restaurant_id, kind, title, body)
  values ('supervisor', p_restaurant, 'booking_new',
          'New booking ' || ref, p_name || ' · ' || p_party || ' guests');
  return ref;
end $$;

revoke all on function public_create_booking(uuid,text,text,text,int,date,time,text,text) from public;
grant execute on function public_create_booking(uuid,text,text,text,int,date,time,text,text) to anon, authenticated;
