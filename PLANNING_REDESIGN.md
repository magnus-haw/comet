# Planning redesign

This revision replaces the standalone Age Projection page with three views over the same planning data:

- **Rooms**: today's roster, classroom start date, age-range signal, actual planned event, incoming/leaving events, and Today/+30/+60 capacity.
- **Center Planning**: cross-room capacity outlook and kindergarten/Vanguard cohort counts.
- **Child Planning**: DOB-derived age milestones, center enrollment date (earliest placement), current room, effective-dated placement history, active plan, and kindergarten cohort.

Key behavioral fixes retained:

- Implementing a move uses the plan's effective (`planned_date`) for placement history rather than the click date.
- Future placements are excluded from current occupancy and included once the projection date reaches their start date.
- A future-effective move implemented early keeps the child in the source room until the effective date.
- Kindergarten eligibility uses a strict September 1 cutoff: the child must already be five before September 1.

Age milestones are advisory only. They do not automatically move children because ACCC rooms have overlapping age ranges and placement decisions include operational/readiness considerations.
