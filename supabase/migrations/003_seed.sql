-- ============================================================================
-- 003 — Seed: permissions catalogue, the five shipped roles, the two branches.
-- Runs as service_role, so the escalation triggers stand down (auth.uid() null).
-- ============================================================================

insert into permissions (key, resource, action, description) values
  ('orders.view','orders','view','See orders'),
  ('orders.view_all','orders','view_all','See every order regardless of owner'),
  ('orders.create','orders','create','Create an order'),
  ('orders.edit','orders','edit','Edit order contents'),
  ('orders.delete','orders','delete','Delete an order'),
  ('orders.assign','orders','assign','Reassign order ownership'),
  ('orders.prioritise','orders','prioritise','Change order priority'),
  ('orders.change_status','orders','change_status','Advance an order through its states'),
  ('orders.override','orders','override','Override the state machine'),
  ('menu.view','menu','view','See the operational menu'),
  ('menu.create','menu','create','Add menu items and categories'),
  ('menu.edit','menu','edit','Edit menu items and categories'),
  ('menu.delete','menu','delete','Delete menu items and categories'),
  ('users.view','users','view','See staff accounts'),
  ('users.create','users','create','Create staff accounts'),
  ('users.edit','users','edit','Edit staff accounts'),
  ('users.delete','users','delete','Delete staff accounts'),
  ('users.assign_role','users','assign_role','Assign roles to staff'),
  ('users.change_password','users','change_password','Reset a staff password'),
  ('roles.view','roles','view','See roles'),
  ('roles.create','roles','create','Create roles'),
  ('roles.edit','roles','edit','Edit roles and their permissions'),
  ('roles.delete','roles','delete','Delete roles'),
  ('restaurants.view','restaurants','view','See restaurants'),
  ('restaurants.edit','restaurants','edit','Edit restaurant details'),
  ('reports.view','reports','view','See reports'),
  ('audit.view','audit','view','Read the audit log'),
  ('settings.manage','settings','manage','Change system settings')
on conflict (key) do nothing;

insert into roles (key, name, description, icon, color, hierarchy_level, is_system) values
  ('superadmin','Superadmin','Owns the system and defines how the organisation works','crown','#811719',0,true),
  ('admin','Admin','Runs both restaurants day to day','shield','#39497C',10,true),
  ('supervisor','Supervisor','The operational safety net on the floor','eye','#B68052',20,true),
  ('chef','Chef','Works the kitchen queue','flame','#8E6238',30,true),
  ('waiter','Waiter','Takes and serves orders','tray','#5E7A6B',40,true)
on conflict (key) do nothing;

-- superadmin: everything
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p where r.key = 'superadmin'
on conflict do nothing;

-- admin: everything except role management and settings; cannot mint peers
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p
where r.key = 'admin' and p.key in (
  'orders.view','orders.view_all','orders.create','orders.edit','orders.assign',
  'orders.prioritise','orders.change_status','menu.view','menu.create','menu.edit',
  'menu.delete','users.view','users.create','users.edit','users.assign_role',
  'users.change_password','roles.view','restaurants.view','restaurants.edit',
  'reports.view','audit.view')
on conflict do nothing;

-- supervisor: operational authority, no user administration
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p
where r.key = 'supervisor' and p.key in (
  'orders.view','orders.view_all','orders.create','orders.edit','orders.assign',
  'orders.prioritise','orders.change_status','orders.override',
  'menu.view','restaurants.view','reports.view')
on conflict do nothing;

-- chef: the kitchen queue and nothing else
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p
where r.key = 'chef' and p.key in ('orders.view','orders.change_status','menu.view')
on conflict do nothing;

-- waiter: take orders, move the ones they own
insert into role_permissions (role_id, permission_id)
select r.id, p.id from roles r cross join permissions p
where r.key = 'waiter' and p.key in
  ('orders.view','orders.create','orders.edit','orders.change_status','menu.view')
on conflict do nothing;

-- pages: navigation is derived from these rows, never from hardcoded lists
insert into role_pages (role_id, page_key, sort_order)
select r.id, x.page, x.ord from roles r join (values
  ('superadmin','dashboard',1),('superadmin','orders',2),('superadmin','menu',3),
  ('superadmin','users',4),('superadmin','roles',5),('superadmin','restaurants',6),
  ('superadmin','reports',7),('superadmin','audit',8),('superadmin','settings',9),
  ('admin','dashboard',1),('admin','orders',2),('admin','menu',3),
  ('admin','users',4),('admin','restaurants',5),('admin','reports',6),('admin','audit',7),
  ('supervisor','monitor',1),('supervisor','orders',2),('supervisor','history',3),
  ('chef','kitchen',1),
  ('waiter','orders',1),('waiter','new-order',2),('waiter','quick-notes',3)
) as x(rkey,page,ord) on x.rkey = r.key
on conflict do nothing;

insert into restaurants (slug, name, address, phone) values
  ('al-muroor','Al Muroor','Al Sa''ada area, Al Rumaithi street, Guardian Towers, Abu Dhabi','02 234 0202'),
  ('al-najda','Al Najda','Mohammed Bin Butti street, facing Al Sultan Bakery, Vision Towers, Abu Dhabi','02 622 6122')
on conflict (slug) do nothing;
