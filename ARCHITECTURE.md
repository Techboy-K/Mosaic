# Mosaic — Phase 0 audit and implementation plan

## 1. What exists today

| Layer | Finding |
|---|---|
| **Framework** | None. Six hand-generated static HTML pages. |
| **Build** | `pages_home.py` + `pages_rest.py` generate the HTML from a shared shell in `build-site.py`. No npm, no bundler, no `package.json`. |
| **Frontend** | Vanilla ES5-compatible JS, 7 modules, ~1,060 lines. No framework. |
| **Backend** | **None.** `serve.py` is a 20-line static dev server. |
| **Database** | **None.** `data/menu.json` (19 categories / 250 items) and `data/delivery-zones.json` are flat files. |
| **Auth** | **None.** |
| **Routing** | Filesystem — `menu.html`, `contact.html`, … |
| **API** | **None.** Everything is `fetch()` against static JSON. |
| **State** | `localStorage` only: `mosaic.cart.v1`, `mosaic.booking.v1`. |
| **Styling** | One design system, `assets/css/site.css`, ~34 CSS custom properties, brand-derived. |
| **Deps** | Three.js + GLTFLoader, vendored locally. Google Fonts via CDN. Nothing else. |
| **Storage** | Local filesystem. 500 dish images, 132 video frames, 6 GLB models, ~39 MB. |
| **Deployment** | None configured. |
| **Env vars** | None. One secret exists: `.secrets/supabase.env` (gitignored). |

### Reusable as-is
- The whole design system. `--wine / --gold / --navy / --cream`, Playfair + PT Sans + Poppins, `.btn`, `.card`, `.fld`, `.formgrid`, `.wheel`. The crew portal extends these tokens; it does not start a second visual language.
- `timewheel.js` — already a clean, reusable component. The crew order screens can use it.
- `menu.json`'s item shape — `{id, name, desc, price, img, url, inStock}` maps 1:1 onto a `menu_items` table. `id` is Mosaic's real WooCommerce product id, so it survives the migration as a stable external key.
- The 500 optimised dish images and the whole `assets/` tree.

### Must be introduced (does not exist)
Server-side auth, a database, an authorization layer, real-time transport, an audit trail. Every security requirement in the brief depends on infrastructure this project does not currently have.

### Must not be touched
The six public pages, `site.css`'s token block, the public cart/booking flows, `assets/img|video|models`.

---

## 2. The one architectural decision

The brief demands server-side authorization, sessions, hashed passwords, RBAC, real-time and audit logs. A static site cannot provide any of it. Two options:

**A. Rewrite as Next.js.** Gives API routes and SSR. Costs: the entire public site is rebuilt, which the brief explicitly forbids.

**B. Keep the static site; add Supabase as the backend.** Postgres + Auth + Row Level Security + Realtime + Storage. The public pages are untouched. `/crew` becomes a new set of pages that talk to Supabase directly, with **RLS enforcing authorization inside the database** — so it holds no matter what the client sends.

**Going with B.** It satisfies "do not rebuild" and "authorization must be server-side" simultaneously. RLS is stronger than app-layer checks: the rules live with the data, so a forged JWT claim or a crafted REST call still cannot read another restaurant's orders.

### Where each requirement lands

| Requirement | Mechanism |
|---|---|
| Password hashing, sessions, reset | Supabase Auth (bcrypt, rotating refresh tokens) |
| Server-side authz | Postgres RLS on every table |
| RBAC, dynamic roles | `roles` / `permissions` / `role_permissions` tables + a `has_perm()` SQL function used by every policy |
| Privilege-escalation prevention | `hierarchy_level` comparison inside DB triggers, not UI |
| System-owner protection | `is_system_owner` boolean + a `BEFORE UPDATE/DELETE` trigger that raises |
| Real-time | Supabase Realtime on `orders`, `order_events`, `notifications` |
| 30-second undo | `order_events.undo_expires_at` — the server decides, never the browser |
| Order state machine | `transition_order()` Postgres function; the only write path to `orders.status` |
| Audit log | `audit_logs`, append-only, `REVOKE UPDATE, DELETE` from all roles |
| Profile uploads | Supabase Storage, private bucket, signed URLs, MIME + magic-byte + size validation |
| Rate limiting / brute force | Supabase Auth built-in, plus a `login_attempts` table |

---

## 3. Schema (17 tables)

```
restaurants ──┬── user_restaurants ──┬── profiles ── auth.users (Supabase)
              │                      └── user_roles ── roles ── role_permissions ── permissions
              ├── menu_categories ── menu_items ── menu_item_modifiers
              └── orders ──┬── order_items
                           ├── order_events        (immutable; carries the undo window)
                           └── order_status_defs   (configurable state machine)
notifications · audit_logs · login_attempts
```

`profiles` extends `auth.users` rather than replacing it, so Supabase owns credentials and we never store a password.

---

## 4. Build order

| Phase | Deliverable | Gate |
|---|---|---|
| 1 | ✅ This audit | — |
| 2 | Supabase project, schema, RLS, seed roles/permissions | Public site still renders |
| 3 | `/crew` login, session, protected shell | Cannot reach `/crew/*` logged out |
| 4 | Dynamic navigation from permissions | Each role sees only its own pages |
| 5 | User management kanban + profile + creation wizard | Admin cannot create an Admin — **tested against the API, not the UI** |
| 6 | Role creation wizard + pyramid visualisation | New role appears in nav without a deploy |
| 7 | Restaurants + switcher | Data isolation holds across restaurants |
| 8 | Menu CMS (migrate the 250 items) | Public `menu.json` still serves |
| 9 | Order model + `transition_order()` | Illegal transitions rejected in SQL |
| 10–12 | Waiter, Chef, Supervisor interfaces | Ownership handoff behaves |
| 13–14 | Realtime + notifications + audio | Two browsers stay in sync |
| 15 | Audit log viewer | Log cannot be edited, even by a superadmin |
| 16–18 | Responsive, security tests, e2e | Escalation suite passes |

Each phase ends by running the app and checking for regressions in the public site.

---

## 5. Deliberately out of scope
Customer accounts, online payment, loyalty, inventory, delivery dispatch, POS/printer integration, analytics. The schema leaves room for them; none is built now.
