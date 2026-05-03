from decimal import Decimal

HOUSEHOLD_PRIORITY = {
    "CV": 100,
    "M": 75,
    "S": 50,
    "P": 25,
}

# should NOT hardcode this long-term
TUITION_RATES = {
    # (room_name, household_type): rate
    ("Infant", "staff"): Decimal("1200.00"),
    ("Infant", "standard"): Decimal("1500.00"),
    ("Toddler", "staff"): Decimal("1000.00"),
    ("Toddler", "standard"): Decimal("1300.00"),
}
