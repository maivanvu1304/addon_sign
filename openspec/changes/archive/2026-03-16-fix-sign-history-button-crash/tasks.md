## 1. Confirm and Prepare

- [x] 1.1 Verify current failure path from button `action_view_sign_history` to invalid `res_model = 'ds.sign.log'`.
- [x] 1.2 Confirm target history data source and filter semantics match existing `sign_history_count` logic.

## 2. Implement Action Fix

- [x] 2.1 Update `action_view_sign_history` to return an action targeting an existing model (`mail.message`).
- [x] 2.2 Apply document-scoped domain filters (`model`, `res_id`, `message_type`) in the returned action.
- [x] 2.3 Ensure action `view_mode` and target behavior open cleanly from the document form stat button.

## 3. Validate Behavior and Compatibility

- [x] 3.1 Test that clicking "Lich su ky" no longer raises model-not-found errors.
- [x] 3.2 Test that history results are scoped to the active `ds.document` only.
- [x] 3.3 Validate count/list consistency between `sign_history_count` and records shown by the action.
- [x] 3.4 Regression test core document states and signing actions (`send sign request`, `finish sign step`, `approve`).

## 4. Documentation and Follow-up

- [x] 4.1 Update module notes/changelog to describe bugfix scope and known trade-off (no dedicated `ds.sign.log` model).
- [x] 4.2 Record a future enhancement item for dedicated audit model if compliance/reporting requires structured sign logs.


