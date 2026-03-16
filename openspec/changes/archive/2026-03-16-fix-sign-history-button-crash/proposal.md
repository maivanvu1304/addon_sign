## Why

The "Lich su ky" button on `ds.document` currently crashes instead of opening a history screen. This blocks users from auditing signing activity and creates uncertainty about workflow completion events.

## What Changes

- Document the current broken behavior:
  - The form stat button `action_view_sign_history` opens an action with `res_model = 'ds.sign.log'`.
  - Model `ds.sign.log` does not exist in the addon, causing a runtime failure when the action is executed.
- Capture suspected root cause:
  - The action appears to reference an old or placeholder model name that was never implemented or was removed.
  - Existing history-like data is already stored in `mail.message` and step-level fields (`ds.document.request.item`), but the action is not aligned with those data sources.
- Define bugfix scope (functional only):
  - Fix the sign-history entry point so clicking the button no longer crashes.
  - Ensure the opened view points to a valid data model and displays meaningful history records for the current document.
  - Keep workflow behavior unchanged (sign/approve transitions are out of scope).
- Define proposed solution direction:
  - First, confirm intended source of truth for sign history.
  - Then either:
    - A) repoint the action to an existing, correct model/view, or
    - B) introduce `ds.sign.log` with minimal required schema and logging hooks.
- Include validation expectations:
  - Button opens successfully for relevant documents.
  - Returned records are filtered by current `document_id`.
  - No regression in document form rendering, chatter, or signing flow.

### Alternative Solutions Considered

- **Alternative 1: Quick repoint to `mail.message`**
  - Pros: fastest recovery, no new model.
  - Cons: generic chatter data may be noisy and not structured as a signing audit log.
- **Alternative 2: Implement dedicated `ds.sign.log` model**
  - Pros: explicit audit domain model, cleaner reporting, future extensibility.
  - Cons: broader change scope (new model, access rules, write points, migration concerns).
- **Selected direction for this change**
  - Keep both paths open during design, with a bias toward the smallest safe fix unless product/compliance requires dedicated audit semantics.

## Capabilities

### New Capabilities
- `sign-history-access`: Ensure the document sign-history action resolves to a valid model and opens a non-crashing, document-scoped history view.

### Modified Capabilities
- None.

## Impact

- Affected code:
  - `custom_addons/sign_dochub/models/ds_document.py` (`action_view_sign_history`)
  - `custom_addons/sign_dochub/views/ds_document_views.xml` (stat button and history page context)
  - Potentially model/view/security files if dedicated log model is chosen.
- Compatibility and risk concerns:
  - If repointing to existing models, risk is mostly data relevance/UX consistency.
  - If adding `ds.sign.log`, risk includes ACL/rule correctness and logging coverage gaps.
  - Any chosen path must preserve existing signing workflow and avoid changing state-transition behavior.

### Validation Checklist

- [ ] Clicking "Lich su ky" no longer raises model-not-found errors.
- [ ] Opened action uses an existing model with readable list/form view.
- [ ] History results are scoped to the active `ds.document`.
- [ ] Existing signing actions (`send sign request`, `finish sign step`, `approve`) remain functional.
- [ ] No regression in form view load for states `draft`, `in_progress`, `adjusting`, and `done`.
