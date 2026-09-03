-- ============================================================================
-- 008 — Fix: superadmin was seeded with the administrative pages only, so the
-- operational ones (kitchen, monitor, history, new-order, quick-notes) hit the
-- denied screen. A superadmin manages everything, so grant every page.
-- Admins gain the monitoring pages too, since they oversee both branches.
-- ============================================================================

insert into role_pages (role_id, page_key, sort_order)
select r.id, x.page, x.ord
from roles r
join (values
  ('dashboard',1),('orders',2),('monitor',3),('kitchen',4),('new-order',5),
  ('quick-notes',6),('history',7),('menu',8),('users',9),('roles',10),
  ('restaurants',11),('reports',12),('audit',13),('settings',14)
) as x(page,ord) on true
where r.key = 'superadmin'
on conflict (role_id, page_key) do update set sort_order = excluded.sort_order;

insert into role_pages (role_id, page_key, sort_order)
select r.id, x.page, x.ord
from roles r
join (values
  ('dashboard',1),('orders',2),('monitor',3),('history',4),('menu',5),
  ('users',6),('restaurants',7),('reports',8),('audit',9)
) as x(page,ord) on true
where r.key = 'admin'
on conflict (role_id, page_key) do update set sort_order = excluded.sort_order;

-- supervisors also need the kitchen view to help when the pass backs up
insert into role_pages (role_id, page_key, sort_order)
select r.id, 'kitchen', 4 from roles r where r.key='supervisor'
on conflict do nothing;
