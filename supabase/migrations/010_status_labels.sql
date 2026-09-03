-- ============================================================================
-- 010 — Shorter status labels. Nine states read as a wall of text on a card;
-- one or two words each is scannable across a busy pass.
-- Keys are unchanged, so nothing that references them breaks.
-- ============================================================================
update order_status_defs set label='Draft'      where key='DRAFT';
update order_status_defs set label='New'        where key='SUBMITTED';
update order_status_defs set label='To kitchen' where key='SENT_TO_KITCHEN';
update order_status_defs set label='Cooking'    where key='IN_PREPARATION';
update order_status_defs set label='Ready'      where key='READY';
update order_status_defs set label='Served'     where key='SERVED';
update order_status_defs set label='Done'       where key='COMPLETED';
update order_status_defs set label='Cancelled'  where key='CANCELLED';
update order_status_defs set label='Attention'  where key='NEEDS_ATTENTION';
