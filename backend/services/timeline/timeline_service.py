"""
timeline_service.py
--------------------
Responsibility:
    Provides chronological sorting and grouping utilities for TimelineEvent records.

Pipeline position:
    Timeline events are created and saved during document processing into the
    `timeline_events` collection. When timeline endpoints are queried
    (GET /api/v1/patients/{patient_id}/timeline), this service organizes
    and validates chronological ordering according to docs/API_CONTRACTS.md Section 19.

Design notes:
    - Pure, focused domain service: does not perform OCR, database writes, or ID generation.
    - Preserves strict date format (YYYY-MM-DD).
    - Unparseable or missing event_dates are safely filtered rather than guessed.
"""

from typing import List, Dict, Any, Optional
from datetime import date as date_type


def sort_timeline(
    events: List[Dict[str, Any]],
    descending: bool = False
) -> List[Dict[str, Any]]:
    """
    Sorts TimelineEvent records chronologically by their `event_date` (YYYY-MM-DD).

    Args:
        events: List of timeline event dictionaries containing an "event_date" field.
        descending: If True, sorts newest first; if False (default), sorts oldest first.

    Returns:
        A new list containing only events with valid dates, sorted in the specified order.
    """
    if not events:
        return []

    valid_events = [e for e in events if _parse_date_safe(e.get("event_date")) is not None]
    return sorted(valid_events, key=lambda e: e["event_date"], reverse=descending)


def build_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience alias for sort_timeline, sorting events in chronological order.
    """
    return sort_timeline(events, descending=False)


def group_by_date(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups timeline events sharing the same event_date for structured display.

    Args:
        events: List of timeline event dictionaries.

    Returns:
        Dict mapping event_date (YYYY-MM-DD) to a list of events on that date.
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        date_key = event.get("event_date")
        if date_key and _parse_date_safe(date_key) is not None:
            grouped.setdefault(date_key, []).append(event)
    return grouped


def filter_by_event_type(
    events: List[Dict[str, Any]],
    event_type: str
) -> List[Dict[str, Any]]:
    """
    Filters timeline events by event_type (e.g., 'diagnosis', 'medication', 'investigation').

    Args:
        events: List of timeline event dictionaries.
        event_type: The target event type string.

    Returns:
        Filtered list of events matching the target event type.
    """
    target = event_type.strip().lower()
    return [e for e in events if str(e.get("event_type", "")).strip().lower() == target]


def _parse_date_safe(date_str: Any) -> Optional[date_type]:
    """
    Safely validates and parses a YYYY-MM-DD date string.
    Returns a datetime.date object or None if invalid.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return date_type.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        return None