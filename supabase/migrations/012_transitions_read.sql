-- 012 — let signed-in staff read the legal-transition map so the kanban can grey
-- out illegal drop targets. transition_order() remains the only writer.
alter table order_transitions enable row level security;
create policy transitions_read on order_transitions for select
  using (auth.uid() is not null);
alter table order_status_defs enable row level security;
create policy status_defs_read on order_status_defs for select
  using (auth.uid() is not null);
