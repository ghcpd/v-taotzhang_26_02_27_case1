# Breadcrumb Ordering Bugfix

This repository contains the Sentry Python SDK and a simple reproduction of a
bug where breadcrumbs appear in the wrong order when their timestamps are
explicitly provided.

## Problem

When developers add breadcrumbs with manually specified timestamps, the SDK
stored them in a `deque` and simply appended them to outgoing events in the
same order. If the timestamps didn't match the order of insertion (e.g. a
breadcrumb from 10 days ago added after one from 5 days ago), the resulting
metric trail in Sentry would be misleading.

The issue was reproduced by the standalone script in the project root
(`test_breadcrumb_ordering.py`), which exercises the behaviour and currently
fails with the production code.

## Solution

The fix sorts the breadcrumbs by their `timestamp` before extending the
`event["breadcrumbs"]["values"]` list in
`basecode/sentry_sdk/scope.py` (`Scope._apply_breadcrumbs_to_event`). The
sorting is performed on a copy of the deque to avoid mutating the scope's
internal buffer and is intentionally tolerant of unexpected data types.

A new pytest-based unit test (`basecode/tests/test_breadcrumb_ordering.py`) was
added to guard against regressions.

## Verifying the fix

1. Run the standalone script from the workspace root:

   ```bash
   python test_breadcrumb_ordering.py
   ```

   The script should now print `PASSED: Breadcrumbs are correctly sorted by
   timestamp.` and exit with code `0`.

2. Run the full test suite inside `basecode`:

   ```bash
   cd basecode
   pytest tests/test_breadcrumb_ordering.py::test_breadcrumbs_are_sorted_by_timestamp
   ```

   or simply `pytest` to execute everything; the new test will exercise the
   ordering logic.

## Notes

- The changelog (`basecode/CHANGELOG.md`) contains an entry documenting the
  bug fix.
- No behaviour changes were made to how breadcrumbs are stored in memory; the
  ordering logic only affects outgoing events.
