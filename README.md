# Breadcrumb Ordering Fix

## Problem
When breadcrumbs were added to Sentry events with different timestamps, they appeared in the wrong order in the final event. If breadcrumbs were added out of chronological order (e.g., adding a message from 5 days ago, then one from 10 days ago), they would remain in insertion order rather than being sorted by timestamp.

This caused confusion when viewing breadcrumb trails in Sentry, as users expected to see events in chronological order (oldest first, newest last), matching the actual sequence of events.

## Root Cause
The issue was in the `_apply_breadcrumbs_to_event` method in [sentry_sdk/scope.py](basecode/sentry_sdk/scope.py#L1296-L1300). This method was simply extending the event's breadcrumbs list with `self._breadcrumbs` (a deque) without sorting them:

```python
# BEFORE (incorrect)
def _apply_breadcrumbs_to_event(self, event, hint, options):
    event.setdefault("breadcrumbs", {}).setdefault("values", []).extend(
        self._breadcrumbs
    )
```

## Solution
Modified the `_apply_breadcrumbs_to_event` method to sort breadcrumbs by their timestamp before adding them to the event:

```python
# AFTER (fixed)
def _apply_breadcrumbs_to_event(self, event, hint, options):
    # Sort breadcrumbs by timestamp to ensure chronological order
    sorted_breadcrumbs = sorted(
        self._breadcrumbs, key=lambda crumb: crumb.get("timestamp", datetime.min)
    )
    event.setdefault("breadcrumbs", {}).setdefault("values", []).extend(
        sorted_breadcrumbs
    )
```

### Key Changes
- **Sorting**: Breadcrumbs are now sorted by their `timestamp` field using Python's `sorted()` function
- **Fallback**: The sort key uses `datetime.min` as a fallback for breadcrumbs without a timestamp (though this shouldn't occur in normal operation)
- **Order**: Breadcrumbs are now guaranteed to appear in chronological order (oldest to newest) in the final event

## Implementation Details
- Each breadcrumb dictionary has a `timestamp` field that stores a datetime object
- The timestamp is set when the breadcrumb is added (in the `add_breadcrumb` method) if not explicitly provided
- Sorting is done just before the breadcrumbs are attached to the event, ensuring correct order regardless of insertion sequence

## Testing
A test script (`test_breadcrumb_ordering.py`) has been provided to verify the fix:

```bash
python test_breadcrumb_ordering.py
```

The test creates three breadcrumbs with out-of-order timestamps and verifies they appear in chronological order in the final event. The test now passes.

## Files Modified
- [basecode/sentry_sdk/scope.py](basecode/sentry_sdk/scope.py) - Updated `_apply_breadcrumbs_to_event` method (lines 1296-1303)

## Impact
- **Performance**: Minimal impact - sorting is done only once when an event is captured, and breadcrumb deques typically contain a small number of items (default max 100)
- **Backward Compatibility**: The change is fully backward compatible - it only affects the order of breadcrumbs in events, not the structure or content
- **User Experience**: Users will now see breadcrumb trails in the correct time order, making it easier to understand the sequence of events leading to an error
