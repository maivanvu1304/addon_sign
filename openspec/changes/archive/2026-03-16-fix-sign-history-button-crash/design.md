## Context

The `ds.document` form exposes a stat button "Lich su ky" that calls `action_view_sign_history`. The action currently points to `res_model = 'ds.sign.log'`, but no such model exists in `sign_dochub`, causing a runtime model resolution error when users click the button.

At the same time, the module already computes `sign_history_count` from `mail.message` entries filtered by:
- `model = 'ds.document'`
- `res_id = <document.id>`
- `message_type = 'notification'`

This indicates the module already has an active history data source, but the button action is out of sync.

## Goals / Non-Goals

**Goals:**
- Remove crash when opening sign history from the document form.
- Ensure the history action targets a valid model and returns document-scoped records.
- Align history action data source with existing `sign_history_count` behavior to avoid user confusion.
- Keep fix small and safe for a bugfix release.

**Non-Goals:**
- Do not introduce a new persistent audit subsystem in this change.
- Do not redesign sign workflow, state transitions, or email/chatter logic.
- Do not backfill or migrate historical records into a new custom log table.

## Decisions

### Decision 1: Treat `ds.sign.log` reference as stale and do not create new model in this change
- **Chosen:** Do not add `ds.sign.log` for this bugfix.
- **Rationale:** The crash is caused by an invalid action target, and existing history data is already available in `mail.message`.
- **Alternative considered:** Create `ds.sign.log` and logging hooks now.
  - Rejected for this change due to expanded scope (new model, ACL/rules, data-write points, and test surface).

### Decision 2: Repoint `action_view_sign_history` to existing history model (`mail.message`)
- **Chosen:** History action should open `mail.message` with the same filter currently used in `sign_history_count`.
- **Rationale:** This provides immediate functional recovery with consistent count/action semantics.
- **Alternative considered:** Repoint to `ds.document.request.item`.
  - Not selected because it represents step state rows, not message-based history already counted by the stat button.

### Decision 3: Preserve UX entry point and keep view behavior minimal
- **Chosen:** Keep the same button and action contract from user perspective; only correct backend target/filter.
- **Rationale:** Avoids UI churn and minimizes regression risk.
- **Alternative considered:** Remove button temporarily.
  - Rejected because it removes expected functionality and loses audit visibility.

## Risks / Trade-offs

- **[Risk] `mail.message` includes non-signing notifications** -> **Mitigation:** Keep strict domain (`model`, `res_id`, `message_type`) and refine filters further if required by UAT.
- **[Risk] Access rights on `mail.message` differ by role** -> **Mitigation:** Validate with both `group_ds_user` and `group_ds_manager` test users.
- **[Trade-off] No dedicated structured sign log model** -> **Mitigation:** Track as future enhancement if compliance/reporting requires richer audit semantics.

## Migration Plan

- No data migration required.
- Deploy as standard module update for `sign_dochub`.
- Rollback strategy: revert action target/filter to prior revision if unexpected access/view issues occur.

## Open Questions

- Should history include only signature-completion events, or all document notification events?
- Is a dedicated `ds.sign.log` needed later for compliance-grade audit reporting?
