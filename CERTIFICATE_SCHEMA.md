# RRC certificate grammar

A Regime Readability Certificate reports a claim **under a stated measurement protocol**. It deliberately separates dimensions that are often merged by phrases such as “stable regime”, “confirmed state”, or “real switch”.

## Four primary fields

### `readability_status`

`identified`, `hidden`, `phantom`, `not_identifiable`, `ambiguous`, `protocol_sensitive`, or `rejected`.

This field answers what the protocol can read. It does not by itself assert generator support.

### `support_scope`

`oracle_asserted`, `not_asserted`, `support_rejected`, or `not_tested`.

This prevents an empirical readout from being silently promoted into a claim about a hidden generator.

### `persistence_status`

`stable`, `protocol_sensitive`, `unstable`, `not_identifiable`, or `not_tested`.

This records whether the readout survives the declared bootstrap or perturbation audit.

### `selection_status`

Examples include `not_selected`, `discovery_only`, `split_confirmed`, `partially_confirmed`, `unadjusted`, `restricted_maxnull_passed`, `null_family_sensitive`, `multi_null_confirmed`, and `not_applicable`.

Multi-null outcomes stay in the selection field; they do not create a fifth “readability” concept.

## Guard status

Guard status is reported separately because “insufficient occupancy / resolution / opportunities” is not equivalent to negative evidence for the state claim.

The JSON Schema is in [`schema/rrc_certificate.schema.json`](schema/rrc_certificate.schema.json).
