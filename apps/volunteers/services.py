from datetime import date

from apps.planning.models import Placement


def month_start(year, month):

    return date(year, month, 1)


def next_month(year, month):

    if month == 12:
        return date(year + 1, 1, 1)

    return date(year, month + 1, 1)


def placement_overlaps_month(
    placement,
    year,
    month,
):

    start = month_start(year, month)

    end = next_month(year, month)

    placement_end = (
        placement.end_date
        or date.max
    )

    return (
        placement.start_date < end
        and placement_end >= start
    )


def months_enrolled_for_ppp_year(
    child,
    ppp_year,
):

    #
    # PPP year:
    #
    # June -> May
    #

    months = []

    #
    # June-Dec
    #

    for month in range(6, 13):

        months.append((ppp_year, month))

    #
    # Jan-May
    #

    for month in range(1, 6):

        months.append((ppp_year + 1, month))

    placements = (
        child.placements.all()
    )

    enrolled_months = 0

    for year, month in months:

        overlaps = any(
            placement_overlaps_month(
                placement,
                year,
                month,
            )
            for placement in placements
        )

        if overlaps:
            enrolled_months += 1

    return enrolled_months

def required_household_hours(
    household,
    ppp_year,
):

    total = 0

    children = household.children.all()

    for child in children:

        total += months_enrolled_for_ppp_year(
            child,
            ppp_year,
        )

    return total







