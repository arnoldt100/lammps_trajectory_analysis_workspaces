# Context - Value Semantics

Status snapshot and decision log for the value-semantics template feature.
Per the ICM rules, this file must be updated whenever the feature's behavior,
data flow, or boundaries change.

Last reviewed: 2026-10-04.

## Implementation Status

### Done

### Pending

### Helper-module structure (from the original plan's Q&A)

Question: should each `ConcreteStateImplementation` class have its own helper
file, or one common helper file?

Decided: hybrid structure. Genuinely shared, type-independent functions live
in one common module (`concrete_state_implementation_helpers.py`, analogous
to `value_object_behaviors.py`); each substantially different owned state
type may get its own helper module when its functions encode type-specific
rules. Helper functions accept explicit state and arguments rather than
depending heavily on one concrete class, keeping testing simple and avoiding
circular imports. Class spelling standardized as
`ConcreteStateImplementation` (capital I); filenames stay snake_case.

### Package-wide behavior decision (finalized)

When behavior is identical for every owned object in a package, use one
stateless package behavior type and pass a behavior instance explicitly to
each wrapper. This keeps the dependency visible at construction while
allowing configured or test-specific implementations. Concrete owned objects
must satisfy the package's behavior contract but do not inherit from the
templates.

`StateValueBehavior` was the default shared behavior; it was removed from
`src` because no production code constructed it, and each caller now
supplies its own `StateValueBehaviorProtocol` implementation directly.
Replacement operations preserve the behavior instance of the original value
object.

## Current Data Flow

```text
domain code defines an owned state type (with validate_state/replace/update)
        │
domain code implements StateValueBehaviorProtocol (stateless)
        │
wrapper constructed: StateValueObject*(state, behavior)
  → behavior.copy_state(state)      (defensive copy in)
  → behavior.validate_state(copied) (delegates to owned object)
        │
property access returns behavior.copy_state(internal)  (defensive copy out)
        │
replace(changes)  → behavior.replace_state(...) → NEW wrapper, same behavior
update(changes)   → behavior.update_state(...)  → validated mutation (mutable)
equality/repr/hash→ behavior.states_equal / state_repr / hash_state
```

No hidden global state: every wrapper holds only its own `_state` and
`_behavior` (private, single underscore, `__slots__`).

## Maintenance Rule

Any change to the public contract (protocols, interface, wrappers, behaviors,
validation, or package layout) requires, in the same change:

1. Updated contract tests under
   `tests/design_patterns_templates/value_semantics/`.
2. An update to `top_level_plan.md` if the contract itself changed.
3. An update to this `context.md` status snapshot.
4. A check of every consumer listed in `README.md`.
