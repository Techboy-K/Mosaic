-- ============================================================================
-- 005 — The order state engine. One entry point, server-side, transactional.
-- ============================================================================

create or replace function can_transition(p_order uuid, p_to text)
returns boolean language plpgsql stable security definer set search_path = public as $$
declare o orders%rowtype; owner_role text; lvl int;
begin
  select * into o from orders where id = p_order;
  if not found then return false; end if;
  if not exists (select 1 from order_transitions
                 where from_status = o.status and to_status = p_to) then
    return false;
  end if;
  if not can_access_restaurant(o.restaurant_id) then return false; end if;

  lvl := auth_level();
  -- supervisors and above may drive any transition they can see
  if has_perm('orders.override') or lvl <= 20 then return true; end if;

  -- otherwise the caller must hold the role that owns the CURRENT state
  select owner_role_key into owner_role from order_status_defs where key = o.status;
  if owner_role is null then return false; end if;
  return exists (
    select 1 from user_roles ur join roles r on r.id = ur.role_id
    where ur.user_id = auth.uid() and r.key = owner_role
  ) and has_perm('orders.change_status');
end $$;

create or replace function transition_order(
  p_order uuid, p_to text, p_meta jsonb default '{}'::jsonb)
returns orders language plpgsql security definer set search_path = public as $$
declare
  o orders%rowtype;
  new_owner uuid;
  owner_role text;
  me_role text;
  undo_until timestamptz;
begin
  select * into o from orders where id = p_order for update;   -- serialise concurrent actors
  if not found then raise exception 'Order not found.' using errcode='P0002'; end if;

  if not can_transition(p_order, p_to) then
    raise exception 'You cannot move this order from % to %.', o.status, p_to
      using errcode='42501';
  end if;

  select owner_role_key into owner_role from order_status_defs where key = p_to;

  -- hand to whoever holds the destination role in this restaurant; the actor
  -- keeps it if they qualify, otherwise it becomes a role-wide queue (null owner)
  if owner_role is null then
    new_owner := null;
  elsif exists (select 1 from user_roles ur join roles r on r.id=ur.role_id
                where ur.user_id = auth.uid() and r.key = owner_role) then
    new_owner := auth.uid();
  else
    new_owner := null;
  end if;

  select r.key into me_role from user_roles ur join roles r on r.id=ur.role_id
   where ur.user_id = auth.uid() order by r.hierarchy_level limit 1;

  -- a handoff to a different role is reversible for 30 seconds
  if owner_role is distinct from (select owner_role_key from order_status_defs where key = o.status)
  then undo_until := now() + interval '30 seconds';
  else undo_until := null; end if;

  perform set_config('mosaic.in_transition','1',true);
  update orders set
    status = p_to,
    owner_id = new_owner,
    submitted_at = case when p_to='SUBMITTED'  then now() else submitted_at end,
    ready_at     = case when p_to='READY'      then now() else ready_at end,
    served_at    = case when p_to='SERVED'     then now() else served_at end,
    completed_at = case when p_to='COMPLETED'  then now() else completed_at end
  where id = p_order returning * into o;
  perform set_config('mosaic.in_transition','0',true);

  insert into order_events (order_id, actor_id, actor_role, action, from_status, to_status,
                            from_owner, to_owner, metadata, undo_expires_at)
  values (p_order, auth.uid(), me_role, 'status_change', o.status, p_to,
          o.owner_id, new_owner, p_meta, undo_until);

  -- tell the receiving role
  if owner_role is not null then
    insert into notifications (role_key, restaurant_id, kind, title, body, order_id)
    values (owner_role, o.restaurant_id,
            case when p_to='READY' then 'order_ready'
                 when p_to='SENT_TO_KITCHEN' then 'order_new' else 'order_moved' end,
            'Order #' || o.number || ' — ' ||
              (select label from order_status_defs where key = p_to),
            coalesce(o.table_label,'') , p_order);
  end if;

  return o;
end $$;

-- ─────────────────────────────────────────────── undo, decided by the server
create or replace function undo_transition(p_event bigint)
returns orders language plpgsql security definer set search_path = public as $$
declare e order_events%rowtype; o orders%rowtype;
begin
  select * into e from order_events where id = p_event for update;
  if not found then raise exception 'No such event.' using errcode='P0002'; end if;
  if e.actor_id <> auth.uid() and not has_perm('orders.override') then
    raise exception 'Only the person who made the change can undo it.' using errcode='42501';
  end if;
  if e.undone_at is not null then
    raise exception 'That change was already undone.' using errcode='42501';
  end if;
  -- the window is evaluated here, against the database clock
  if e.undo_expires_at is null or now() > e.undo_expires_at then
    raise exception 'The undo window has closed.' using errcode='42501';
  end if;

  perform set_config('mosaic.in_transition','1',true);
  update orders set status = e.from_status, owner_id = e.from_owner
   where id = e.order_id returning * into o;
  perform set_config('mosaic.in_transition','0',true);

  update order_events set undone_at = now() where id = p_event;
  insert into order_events (order_id, actor_id, action, from_status, to_status,
                            from_owner, to_owner, metadata)
  values (e.order_id, auth.uid(), 'undo', e.to_status, e.from_status,
          e.to_owner, e.from_owner, jsonb_build_object('undid_event', p_event));
  return o;
end $$;

create or replace function set_order_priority(p_order uuid, p_priority text)
returns orders language plpgsql security definer set search_path = public as $$
declare o orders%rowtype; old text;
begin
  if not has_perm('orders.prioritise') then
    raise exception 'You cannot change priority.' using errcode='42501';
  end if;
  select * into o from orders where id = p_order for update;
  if not can_access_restaurant(o.restaurant_id) then
    raise exception 'Not your restaurant.' using errcode='42501';
  end if;
  old := o.priority;
  update orders set priority = p_priority where id = p_order returning * into o;
  insert into order_events (order_id, actor_id, action, metadata)
  values (p_order, auth.uid(), 'priority_change',
          jsonb_build_object('from', old, 'to', p_priority));
  insert into notifications (role_key, restaurant_id, kind, title, order_id)
  values ('chef', o.restaurant_id, 'priority',
          'Order #' || o.number || ' is now ' || p_priority, p_order);
  return o;
end $$;

create or replace function reassign_order(p_order uuid, p_owner uuid)
returns orders language plpgsql security definer set search_path = public as $$
declare o orders%rowtype;
begin
  if not has_perm('orders.assign') then
    raise exception 'You cannot reassign orders.' using errcode='42501';
  end if;
  select * into o from orders where id = p_order for update;
  if not can_access_restaurant(o.restaurant_id) then
    raise exception 'Not your restaurant.' using errcode='42501';
  end if;
  insert into order_events (order_id, actor_id, action, from_owner, to_owner)
  values (p_order, auth.uid(), 'reassign', o.owner_id, p_owner);
  update orders set owner_id = p_owner where id = p_order returning * into o;
  return o;
end $$;
