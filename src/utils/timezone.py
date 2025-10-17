"""
Timezone utilities for Singapore Time (SGT)
"""
from datetime import datetime
import pytz

# Singapore timezone
SGT = pytz.timezone('Asia/Singapore')


def get_singapore_time() -> datetime:
    """
    Get current time in Singapore timezone

    Returns:
        datetime: Current datetime in SGT
    """
    return datetime.now(SGT)


def format_datetime(dt, format_str: str = "%Y-%m-%d %I:%M %p") -> str:
    """
    Format a datetime object or ISO string to a string in Singapore timezone

    Args:
        dt: Datetime object or ISO string to format
        format_str: Format string (default: "2025-10-18 02:30 PM")

    Returns:
        str: Formatted datetime string
    """
    # Handle string input (ISO format from database)
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt)

    # Convert to Singapore time
    sgt_time = dt.astimezone(SGT)
    return sgt_time.strftime(format_str)


def format_date(dt: datetime) -> str:
    """
    Format date only (e.g., "18 Oct 2025")

    Args:
        dt: Datetime object

    Returns:
        str: Formatted date string
    """
    return format_datetime(dt, "%d %b %Y")


def format_time(dt: datetime) -> str:
    """
    Format time only (e.g., "02:30 PM")

    Args:
        dt: Datetime object

    Returns:
        str: Formatted time string
    """
    return format_datetime(dt, "%I:%M %p")


def format_full_datetime(dt: datetime) -> str:
    """
    Format full date and time (e.g., "18 Oct 2025, 02:30 PM")

    Args:
        dt: Datetime object

    Returns:
        str: Formatted datetime string
    """
    return format_datetime(dt, "%d %b %Y, %I:%M %p")
