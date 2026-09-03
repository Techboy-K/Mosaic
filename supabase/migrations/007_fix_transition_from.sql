-- ============================================================================
-- 007 — Fix: transition_order() recorded from_status AFTER the update, so the
-- RETURNING clause had already overwritten the row variable. Events stored
-- from_status == to_status, which made undo a no-op.
-- Capture the previous state into its own variables first.
-- ============================================================================
create or replace function transition_order(
  p_order uuid, p_to text, p_meta jsonb default '{}'::jsonb)
returns orders language plpgsql security definer set search_path = public as $$
declare
  o            orders%rowtype;
  prev_status  text;
  prev_owner   uuid;
  prev_role    text;
  new_owner    uuid;
  owner_role   text;
  me_role      text;
  undo_until   timestamptz;
begin
  select * into o from orders where id = p_order for update;
  if not found then raise exception 'Order not found.' using errcode='P0002'; end if;

  if not can_transition(p_order, p_to) then
    raise exception 'You cannot move this order from % to %.', o.status, p_to
      using errcode='42501';
  end if;

  -- snapshot BEFORE the update, or RETURNING clobbers it
  prev_status := o.status;
  prev_owner  := o.owner_id;
  select owner_role_key into prev_role from order_status_defs where key = prev_status;
  select owner_role_key into owner_role from order_status_defs where key = p_to;

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

  if owner_role is distinct from prev_role
    then undo_until := now() + interval '30 seconds';
    else undo_until := null;
  end if;

  perform set_config('mosaic.in_transition','1',true);
  update orders set
    status = p_to,
    owner_id = new_owner,
    submitted_at = case when p_to='SUBMITTED' then now() else submitted_at end,
    ready_at     = case when p_to='READY'     then now() else ready_at end,
    served_at    = case when p_to='SERVED'    then now() else served_at end,
    completed_at = case when p_to='COMPLETED' then now() else completed_at end
  where id = p_order returning * into o;
  perform set_config('mosaic.in_transition','0',true);

  insert into order_events (order_id, actor_id, actor_role, action, from_status, to_status,
                            from_owner, to_owner, metadata, undo_expires_at)
  values (p_order, auth.uid(), me_role, 'status_change', prev_status, p_to,
          prev_owner, new_owner, p_meta, undo_until);

  if owner_role is not null then
    insert into notifications (role_key, restaurant_id, kind, title, body, order_id)
    values (owner_role, o.restaurant_id,
            case when p_to='READY' then 'order_ready'
                 when p_to='SENT_TO_KITCHEN' then 'order_new' else 'order_moved' end,
            'Order #' || o.number || ' — ' ||
              (select label from order_status_defs where key = p_to),
            coalesce(o.table_label,''), p_order);
  end if;

  return o;
end $$;
