## ADDED Requirements

### Requirement: History action SHALL resolve to a valid model
The system SHALL open sign history from the `ds.document` form without model resolution errors.

#### Scenario: User opens sign history from document form
- **WHEN** a user clicks the "Lich su ky" button on a `ds.document` record
- **THEN** the server SHALL return an `ir.actions.act_window` targeting an existing model
- **AND** the client SHALL render the history view without raising a "model does not exist" error

### Requirement: History action SHALL be document-scoped
The sign history action SHALL show only history records associated with the active document.

#### Scenario: Action domain filters by active document
- **WHEN** the history action is built for document `D`
- **THEN** the action domain SHALL include constraints that limit results to `D`
- **AND** records from other documents SHALL NOT appear in the result set

### Requirement: History count and history action SHALL use consistent selection criteria
The stat button count and opened history list SHALL refer to the same class of records.

#### Scenario: Count/list consistency
- **WHEN** a user sees the "Lich su ky" stat value and opens the history action
- **THEN** both features SHALL rely on the same base filter semantics
- **AND** users SHALL NOT see a materially unrelated dataset after clicking the stat button
