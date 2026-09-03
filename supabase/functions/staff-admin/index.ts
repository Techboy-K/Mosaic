// ============================================================================
// staff-admin — privileged staff operations.
//
// Creating an auth user, sending an invite and resetting a password all need
// the service-role key, which must never reach a browser. This function holds
// it server-side and re-derives the caller's authority from their JWT before
// doing anything. It never trusts a role, level or restaurant id from the body.
// ============================================================================
import { createClient } from 'jsr:@supabase/supabase-js@2';

const URL  = Deno.env.get('SUPABASE_URL')!;
const ANON = Deno.env.get('SUPABASE_ANON_KEY')!;
const SVC  = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status, headers: { ...cors, 'Content-Type': 'application/json' },
  });

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  if (req.method !== 'POST')    return json({ error: 'POST only' }, 405);

  const jwt = (req.headers.get('Authorization') ?? '').replace('Bearer ', '');
  if (!jwt) return json({ error: 'Not signed in' }, 401);

  // caller-scoped client: RLS applies, so this cannot see more than they can
  const asCaller = createClient(URL, ANON, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
  });
  const admin = createClient(URL, SVC, { auth: { persistSession: false } });

  const { data: { user } } = await asCaller.auth.getUser();
  if (!user) return json({ error: 'Not signed in' }, 401);

  // authority is derived here, never accepted from the client
  const { data: me } = await admin.from('profiles')
    .select('id, email, is_active, is_system_owner').eq('id', user.id).single();
  if (!me?.is_active) return json({ error: 'Account is not active' }, 403);

  const { data: myRoles } = await admin.from('user_roles')
    .select('roles(key, name, hierarchy_level)').eq('user_id', user.id);
  const levels = (myRoles ?? []).map((r: any) => r.roles?.hierarchy_level ?? 9999);
  const myLevel = levels.length ? Math.min(...levels) : 9999;
  const myRoleName = (myRoles ?? [])[0]?.roles?.name ?? '—';

  const { data: myPerms } = await admin.from('role_permissions')
    .select('permissions(key), roles!inner(user_roles!inner(user_id))')
    .eq('roles.user_roles.user_id', user.id);
  const perms = new Set((myPerms ?? []).map((p: any) => p.permissions?.key).filter(Boolean));
  const can = (p: string) => perms.has(p);

  const body = await req.json().catch(() => ({}));
  const action = body.action as string;

  const audit = (a: string, resource: string, rid: string | null, before: unknown, after: unknown) =>
    admin.from('audit_logs').insert({
      actor_id: me.id, actor_email: me.email, actor_role: myRoleName,
      action: a, resource, resource_id: rid, before, after,
    });

  try {
    // ─────────────────────────────────────────── create or invite a staff member
    if (action === 'create_user') {
      if (!can('users.create')) return json({ error: 'You cannot create staff.' }, 403);

      const { email, full_name, role_id, restaurant_ids, mode, password } = body;
      if (!email || !role_id) return json({ error: 'Email and role are required.' }, 400);

      const { data: role } = await admin.from('roles')
        .select('id, name, hierarchy_level, is_active').eq('id', role_id).single();
      if (!role?.is_active) return json({ error: 'That role does not exist.' }, 400);

      // the escalation rule, enforced here as well as in the DB trigger
      if (role.hierarchy_level <= myLevel) {
        return json({ error:
          `You cannot create a ${role.name}. It sits at or above your own authority.` }, 403);
      }
      if (!can('users.assign_role')) return json({ error: 'You cannot assign roles.' }, 403);

      let created;
      if (mode === 'invite') {
        const r = await admin.auth.admin.inviteUserByEmail(email, {
          redirectTo: `${body.origin ?? ''}/crew/reset.html`,
        });
        if (r.error) return json({ error: r.error.message }, 400);
        created = r.data.user;
      } else {
        if (!password || String(password).length < 10) {
          return json({ error: 'A temporary password must be at least 10 characters.' }, 400);
        }
        const r = await admin.auth.admin.createUser({
          email, password, email_confirm: true,
          user_metadata: { must_change_password: true },
        });
        if (r.error) return json({ error: r.error.message }, 400);
        created = r.data.user;
      }

      await admin.from('profiles').upsert({
        id: created!.id, email, full_name: full_name ?? '', created_by: me.id,
      });
      await admin.from('user_roles').insert({
        user_id: created!.id, role_id, assigned_by: me.id,
      });

      // a caller may only grant restaurants they hold themselves
      let allowed: string[] = restaurant_ids ?? [];
      if (myLevel !== 0) {
        const { data: mine } = await admin.from('user_restaurants')
          .select('restaurant_id').eq('user_id', me.id);
        const mineSet = new Set((mine ?? []).map((r: any) => r.restaurant_id));
        allowed = allowed.filter((r) => mineSet.has(r));
      }
      if (allowed.length) {
        await admin.from('user_restaurants').insert(
          allowed.map((rid: string) => ({ user_id: created!.id, restaurant_id: rid })));
      }

      await audit('user.created', 'profiles', created!.id, null,
        { email, full_name, role: role.name, restaurants: allowed.length, mode });
      return json({ ok: true, user_id: created!.id, mode });
    }

    // ─────────────────────────────────────────── set a password for someone else
    if (action === 'set_password') {
      if (!can('users.change_password')) return json({ error: 'You cannot change passwords.' }, 403);
      const { user_id, password } = body;
      if (!password || String(password).length < 10) {
        return json({ error: 'Password must be at least 10 characters.' }, 400);
      }
      const { data: target } = await admin.from('profiles')
        .select('id, email, is_system_owner').eq('id', user_id).single();
      if (!target) return json({ error: 'No such user.' }, 404);
      if (target.is_system_owner && !me.is_system_owner) {
        return json({ error: 'Only a system owner can change a system owner password.' }, 403);
      }
      const { data: tr } = await admin.from('user_roles')
        .select('roles(hierarchy_level)').eq('user_id', user_id);
      const tLevel = Math.min(...((tr ?? []).map((r: any) => r.roles?.hierarchy_level ?? 9999)), 9999);
      if (tLevel <= myLevel && user_id !== me.id) {
        return json({ error: 'You cannot change the password of someone at or above your authority.' }, 403);
      }
      const r = await admin.auth.admin.updateUserById(user_id, { password });
      if (r.error) return json({ error: r.error.message }, 400);
      await audit('user.password_changed', 'profiles', user_id, null, { by: me.email });
      return json({ ok: true });
    }

    // ─────────────────────────────────────────── enable / disable
    if (action === 'set_active') {
      if (!can('users.edit')) return json({ error: 'You cannot edit staff.' }, 403);
      const { user_id, is_active } = body;
      const { data: target } = await admin.from('profiles')
        .select('id, email, is_active, is_system_owner').eq('id', user_id).single();
      if (!target) return json({ error: 'No such user.' }, 404);
      if (target.is_system_owner) return json({ error: 'The system owner cannot be disabled.' }, 403);
      const { data: tr } = await admin.from('user_roles')
        .select('roles(hierarchy_level)').eq('user_id', user_id);
      const tLevel = Math.min(...((tr ?? []).map((r: any) => r.roles?.hierarchy_level ?? 9999)), 9999);
      if (tLevel <= myLevel) return json({ error: 'That user is at or above your authority.' }, 403);

      await admin.from('profiles').update({ is_active }).eq('id', user_id);
      await audit(is_active ? 'user.enabled' : 'user.disabled', 'profiles', user_id,
        { is_active: target.is_active }, { is_active });
      return json({ ok: true });
    }

    // ─────────────────────────────────────────── move a user to another role
    if (action === 'set_role') {
      if (!can('users.assign_role')) return json({ error: 'You cannot assign roles.' }, 403);
      const { user_id, role_id } = body;
      const { data: role } = await admin.from('roles')
        .select('id, name, hierarchy_level').eq('id', role_id).single();
      if (!role) return json({ error: 'No such role.' }, 400);
      if (role.hierarchy_level <= myLevel) {
        return json({ error:
          `You cannot move anyone into ${role.name} — it is at or above your authority.` }, 403);
      }
      const { data: target } = await admin.from('profiles')
        .select('id, email, is_system_owner').eq('id', user_id).single();
      if (target?.is_system_owner) return json({ error: 'The system owner role cannot change.' }, 403);

      const { data: tr } = await admin.from('user_roles')
        .select('role_id, roles(name, hierarchy_level)').eq('user_id', user_id);
      const tLevel = Math.min(...((tr ?? []).map((r: any) => r.roles?.hierarchy_level ?? 9999)), 9999);
      if (tLevel <= myLevel) return json({ error: 'That user is at or above your authority.' }, 403);

      await admin.from('user_roles').delete().eq('user_id', user_id);
      await admin.from('user_roles').insert({ user_id, role_id, assigned_by: me.id });
      await audit('user.role_changed', 'profiles', user_id,
        { role: (tr ?? [])[0]?.roles?.name }, { role: role.name });
      return json({ ok: true });
    }

    return json({ error: 'Unknown action' }, 400);
  } catch (e) {
    return json({ error: String(e).slice(0, 200) }, 500);
  }
});
