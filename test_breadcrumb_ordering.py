"""
Test script to verify that breadcrumbs are correctly ordered by timestamp when sent.

When breadcrumbs are added at different times or with different timestamps,
they should be sorted chronologically in the final event, regardless of the
order in which they were added.
"""

import datetime
import sys
import os

# Add the basecode path to test against the main codebase
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "basecode"))

import sentry_sdk
from sentry_sdk import add_breadcrumb, capture_exception


def parse_timestamp(ts_str):
    """Parse ISO format timestamp string to datetime."""
    ts_str = ts_str.replace("Z", "")
    try:
        return datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")


def test_breadcrumb_ordering():
    """
    Test that breadcrumbs are sorted by timestamp in the final event.
    
    This test adds breadcrumbs with out-of-order timestamps and verifies
    that when an event is captured, the breadcrumbs appear in chronological
    order (oldest first, newest last).
    """
    events = []
    
    def capture_event(event, hint):
        events.append(event)
        return None  # Don't send to Sentry
    
    sentry_sdk.init(
        dsn="https://00000000000000000000000000000000@o0.ingest.sentry.io/0",
        before_send=capture_event,
    )
    
    # Create timestamps intentionally out of order
    base_time = datetime.datetime.now()
    timestamps = [
        base_time - datetime.timedelta(days=5),   # middle
        base_time - datetime.timedelta(days=10),  # oldest
        base_time - datetime.timedelta(days=1),   # newest
    ]
    
    # Add breadcrumbs in non-chronological order with unique category
    test_category = "test_ordering"
    for i, ts in enumerate(timestamps):
        add_breadcrumb(
            message=f"Event at {ts.isoformat()}",
            category=test_category,
            level="info",
            timestamp=ts,
        )
    
    # Capture an exception to trigger event creation
    try:
        raise ValueError("Test exception")
    except ValueError:
        capture_exception()
    
    assert len(events) == 1, "Expected exactly one event"
    event = events[0]
    
    assert "breadcrumbs" in event, "Event should contain breadcrumbs"
    assert "values" in event["breadcrumbs"], "Breadcrumbs should have values"
    
    # Filter only our test breadcrumbs
    breadcrumb_values = [
        bc for bc in event["breadcrumbs"]["values"] 
        if bc.get("category") == test_category
    ]
    assert len(breadcrumb_values) == 3, f"Expected 3 test breadcrumbs, got {len(breadcrumb_values)}"
    
    # Extract timestamps from breadcrumbs
    breadcrumb_timestamps = [parse_timestamp(bc["timestamp"]) for bc in breadcrumb_values]
    
    # Verify breadcrumbs are sorted chronologically
    sorted_timestamps = sorted(breadcrumb_timestamps)
    
    if breadcrumb_timestamps != sorted_timestamps:
        print("FAILED: Breadcrumbs are not sorted by timestamp!")
        print(f"  Expected order: {[ts.isoformat() for ts in sorted_timestamps]}")
        print(f"  Actual order:   {[ts.isoformat() for ts in breadcrumb_timestamps]}")
        return False
    
    print("PASSED: Breadcrumbs are correctly sorted by timestamp.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Breadcrumb Ordering")
    print("=" * 60)
    print()
    
    print("Test: Breadcrumb ordering by timestamp")
    print("-" * 40)
    result = test_breadcrumb_ordering()
    print()
    
    print("=" * 60)
    if result:
        print("All tests PASSED!")
        sys.exit(0)
    else:
        print("Test FAILED!")
        sys.exit(1)
