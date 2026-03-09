from datetime import date


def child_moveup_status(child, room):
    """
    Determine move-up readiness relative to the room age limits.

    Returns:
        status_code, label
    """

    today = date.today()

    age_months = (
        (today.year - child.birth_date.year) * 12
        + (today.month - child.birth_date.month)
    )

    max_age = room.max_age_months
    min_age = room.min_age_months

    if age_months > max_age:
        return "overdue", "Overdue"

    if age_months >= max_age - 2:
        return "approaching", "Approaching"

    if age_months >= min_age:
        return "ready", "Eligible"

    return "early", "Too Young"
