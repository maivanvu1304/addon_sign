# Changelog

## Unreleased

### Fixed
- Prevented crash when clicking the `Lich su ky` button on `ds.document` by replacing invalid action target `ds.sign.log` with `mail.message`.
- Aligned sign-history action filters with `sign_history_count` semantics:
  - `model = 'ds.document'`
  - `res_id = <document_id>`
  - `message_type = 'notification'`

### Notes
- This bugfix does not introduce a dedicated sign audit model. History currently uses existing chatter notifications.

### Future Enhancement
- Evaluate introducing a dedicated `ds.sign.log` model for structured, compliance-oriented signing audit records.
