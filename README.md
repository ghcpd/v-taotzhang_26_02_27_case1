# Breadcrumb Ordering Fix

## What was wrong
Breadcrumbs added to the Sentry SDK were stored in insertion order and sent exactly as kept in the internal breadcrumb buffer. When breadcrumbs were added out of chronological order (e.g., replaying a past event), the event payload would still show them out of order.

## What was changed
- Updated `sentry_sdk/scope.py` so that breadcrumbs are **sorted by their `timestamp`** before being attached to an outgoing event.
- This ensures the breadcrumb list in the final event is always displayed as a proper timeline (oldest first, newest last), regardless of the order they were added.

## How to validate
Run the provided test script:

```bash
python test_breadcrumb_ordering.py
```

It should print **"PASSED: Breadcrumbs are correctly sorted by timestamp."** and exit with code 0.
