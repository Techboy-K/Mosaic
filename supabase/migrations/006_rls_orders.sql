-- ============================================================================
-- 006 — RLS for menu, orders, events, notifications. Restaurant isolation is
-- enforced here, so a crafted request cannot read another branch's data.
-- ============================================================================
alter table menu_categories     enable row level security;
alter table menu_items          enable row level security;
alter table menu_item_modifiers enable row level security;
alter table order_status_defs   enable row level security;
alter table order_transitions   enable row level security;
alter table orders              enable row level security;
alter table order_items         enable row level security;
alter table order_events        enable row level security;
alter table notifications       enable row level security;

-- menu: anyone signed in with menu.view may read their restaurants' menu
create policy menu_cat_read on menu_categories for select
  using (has_perm('menu.view') and (restaurant_id is null or can_access_restaurant(restaurant_id)));
create policy menu_cat_write on menu_categories for all
  using (has_perm('menu.edit') and (restaurant_id is null or can_access_restaurant(restaurant_id)))
  with check (has_perm('menu.edit') and (restaurant_id is null or can_access_restaurant(restaurant_id)));

create policy menu_item_read on menu_items for select
  using (has_perm('menu.view') and (restaurant_id is null or can_access_restaurant(restaurant_id)));
create policy menu_item_write on menu_items for all
  using (has_perm('menu.edit') and (restaurant_id is null or can_access_restaurant(restaurant_id)))
  with check (has_perm('menu.edit') and (restaurant_id is null or can_access_restaurant(restaurant_id)));

create policy mod_read on menu_item_modifiers for select using (has_perm('menu.view'));
create policy mod_write on menu_item_modifiers for all
  using (has_perm('menu.edit')) with check (has_perm('menu.edit'));

create policy statusdef_read on order_status_defs for select using (auth.uid() is not null);
create policy trans_read     on order_transitions for select using (auth.uid() is not null);

-- orders: your restaurant, and either yours or you can see everything
create policy orders_read on orders for select
  using (can_access_restaurant(restaurant_id)
         and (has_perm('orders.view_all') or owner_id = auth.uid() or created_by = auth.uid()
              or owner_id is null));
create policy orders_create on orders for insert
  with check (has_perm('orders.create') and can_access_restaurant(restaurant_id)
              and created_by = auth.uid());
-- contents stay editable; STATUS is protected by the trigger regardless
create policy orders_update on orders for update
  using (can_access_restaurant(restaurant_id)
         and (has_perm('orders.override') or owner_id = auth.uid() or created_by = auth.uid()))
  with check (can_access_restaurant(restaurant_id));
create policy orders_delete on orders for delete
  using (has_perm('orders.delete') and can_access_restaurant(restaurant_id));

create policy oitems_read on order_items for select
  using (exists (select 1 from orders o where o.id = order_id
                 and can_access_restaurant(o.restaurant_id)));
create policy oitems_write on order_items for all
  using (exists (select 1 from orders o where o.id = order_id
                 and can_access_restaurant(o.restaurant_id)
                 and (has_perm('orders.override') or o.owner_id = auth.uid()
                      or o.created_by = auth.uid())))
  with check (exists (select 1 from orders o where o.id = order_id
                 and can_access_restaurant(o.restaurant_id)));

-- the trail is readable, never writable from the client
create policy oevents_read on order_events for select
  using (exists (select 1 from orders o where o.id = order_id
                 and can_access_restaurant(o.restaurant_id)));
revoke insert, update, delete on order_events from authenticated, anon;

create policy notif_read on notifications for select
  using (user_id = auth.uid()
      or (role_key is not null
          and exists (select 1 from user_roles ur join roles r on r.id=ur.role_id
                      where ur.user_id = auth.uid() and r.key = notifications.role_key)
          and (restaurant_id is null or can_access_restaurant(restaurant_id))));
create policy notif_update on notifications for update
  using (user_id = auth.uid()
      or (role_key is not null
          and exists (select 1 from user_roles ur join roles r on r.id=ur.role_id
                      where ur.user_id = auth.uid() and r.key = notifications.role_key)))
  with check (true);

-- realtime
alter publication supabase_realtime add table orders;
alter publication supabase_realtime add table order_events;
alter publication supabase_realtime add table notifications;
