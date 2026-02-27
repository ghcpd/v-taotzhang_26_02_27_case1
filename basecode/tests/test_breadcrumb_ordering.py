import datetime

import pytest

from sentry_sdk import add_breadcrumb, capture_exception


def test_breadcrumbs_are_sorted_by_timestamp(sentry_init, capture_events):
    """Breadcrumbs should always be chronologically ordered in an event.

    It is possible to add crumbs with an explicit ``timestamp`` that doesn't
    reflect the order in which they were added. Prior to the bug fix these
    crumbs were sent in insertion order which made the trail confusing in the
    Sentry UI. This test reproduces the problem by adding three breadcrumbs in
    non-chronological order and asserts that the resulting event has them
    sorted oldest-to-newest.
    """

    sentry_init({})
    events = capture_events()

    base_time = datetime.datetime.now()
    timestamps = [
        base_time - datetime.timedelta(days=5),
        base_time - datetime.timedelta(days=10),
        base_time - datetime.timedelta(days=1),
    ]

    category = "test_ordering"
    for ts in timestamps:
        add_breadcrumb(
            message=f"Event at {ts.isoformat()}",
            category=category,
            level="info",
            timestamp=ts,
        )

    try:
        raise ValueError("Test exception")
    except ValueError:
        capture_exception()

    assert len(events) == 1
    event = events[0]
    assert "breadcrumbs" in event
    assert "values" in event["breadcrumbs"]

    crumbs = [
        bc for bc in event["breadcrumbs"]["values"] if bc.get("category") == category
    ]
    assert len(crumbs) == 3

    timestamps_out = [bc["timestamp"] for bc in crumbs]
    # iso formatted timestamps lexicographically sort the same as chronological
    assert timestamps_out == sorted(timestamps_out)
