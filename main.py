"""
main.py — demo for sorting, filtering, recurring tasks, and conflict detection.
Run with: python main.py
"""

from datetime import date, time, datetime, timedelta
from pawpal_system import (
    Owner, Pet, Task, TimeBlock, Scheduler,
    Priority, Frequency, Species, Schedule, ScheduledTask,
)

# ---------------------------------------------------------------------------
# Setup: owner + two pets
# ---------------------------------------------------------------------------
jordan = Owner(
    id=1,
    name="Jordan",
    available_times=[
        TimeBlock(start=time(8, 0),  end=time(10, 0)),
        TimeBlock(start=time(17, 0), end=time(19, 0)),
    ],
)

mochi = Pet(id=1, name="Mochi", species=Species.DOG, age=3)
luna  = Pet(id=2, name="Luna",  species=Species.CAT, age=5)

# Add tasks OUT OF ORDER (preferred_time is not sorted) to test sorting
mochi.add_task(Task(id=3, title="Grooming",       duration_mins=20, priority=Priority.LOW,    frequency=Frequency.WEEKLY))
mochi.add_task(Task(id=1, title="Morning walk",   duration_mins=30, priority=Priority.HIGH,   frequency=Frequency.DAILY,  preferred_time=time(8, 0)))
mochi.add_task(Task(id=2, title="Breakfast",      duration_mins=10, priority=Priority.HIGH,   frequency=Frequency.DAILY,  preferred_time=time(8, 30)))

luna.add_task(Task(id=6,  title="Evening feeding", duration_mins=10, priority=Priority.HIGH,   frequency=Frequency.DAILY,  preferred_time=time(17, 30)))
luna.add_task(Task(id=4,  title="Medication",      duration_mins=5,  priority=Priority.HIGH,   frequency=Frequency.DAILY,  preferred_time=time(8, 0)))
luna.add_task(Task(id=5,  title="Playtime",        duration_mins=15, priority=Priority.MEDIUM, frequency=Frequency.DAILY,  preferred_time=time(17, 0)))

jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)

# ---------------------------------------------------------------------------
# Step 2a: Sort tasks by preferred time
# ---------------------------------------------------------------------------
print("=" * 55)
print("STEP 2A — Sort all tasks by preferred time")
print("=" * 55)

all_tasks = [task for pet in jordan.get_pets() for task in pet.tasks]
sorted_tasks = scheduler.sort_tasks_by_time(all_tasks)

for t in sorted_tasks:
    pref = t.preferred_time.strftime("%I:%M %p") if t.preferred_time else "(no preferred time)"
    print(f"  {pref:12}  [{t.priority.name:6}]  {t.title}")

# ---------------------------------------------------------------------------
# Step 2b: Filter tasks
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("STEP 2B — Filter: only Mochi's pending tasks")
print("=" * 55)

for pet, task in scheduler.filter_tasks(pet_name="Mochi", completed=False):
    print(f"  {pet.name}: {task.title} ({task.priority.name})")

print()
print("Filter: all completed tasks (none yet — should be empty)")
completed_pairs = scheduler.filter_tasks(completed=True)
if not completed_pairs:
    print("  (no completed tasks)")

# ---------------------------------------------------------------------------
# Step 3: Recurring task — complete one and verify next occurrence is created
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("STEP 3 — Recurring task: complete 'Morning walk'")
print("=" * 55)

walk = next(t for t in mochi.tasks if t.title == "Morning walk")
print(f"  Before: '{walk.title}' completed={walk.is_completed}, tasks count={len(mochi.tasks)}")

next_walk = scheduler.complete_task(mochi, walk)

print(f"  After:  '{walk.title}' completed={walk.is_completed}")
if next_walk:
    print(f"  New recurring instance: '{next_walk.title}' due {next_walk.due_date} (today + 1 day via timedelta)")
print(f"  Mochi now has {len(mochi.tasks)} tasks total")

# Also check the filter now picks up the completed task
completed_pairs = scheduler.filter_tasks(completed=True)
print(f"  Completed tasks filter now returns {len(completed_pairs)} task(s)")

# ---------------------------------------------------------------------------
# Step 4: Conflict detection — build a Schedule with two overlapping tasks
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("STEP 4 — Conflict detection")
print("=" * 55)

today = date.today()
conflict_schedule = Schedule(date=today, owner=jordan)

t_a = Task(id=90, title="Bath time",     duration_mins=30, priority=Priority.MEDIUM, frequency=Frequency.ONCE)
t_b = Task(id=91, title="Nail trimming", duration_mins=20, priority=Priority.LOW,    frequency=Frequency.ONCE)

# Intentionally place both at the same start time so they overlap
overlap_start = datetime.combine(today, time(9, 0))
conflict_schedule.add_scheduled_task(ScheduledTask(task=t_a, pet=mochi, scheduled_time=overlap_start))
conflict_schedule.add_scheduled_task(ScheduledTask(task=t_b, pet=luna,  scheduled_time=overlap_start))

warnings = conflict_schedule.detect_conflicts()
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts detected.")

# ---------------------------------------------------------------------------
# Step 5: Generate today's real schedule (conflict-free via _find_slot)
# ---------------------------------------------------------------------------
print()
print("=" * 55)
print("STEP 5 — Full schedule (conflict-free via scheduler)")
print("=" * 55)

schedule = scheduler.generate_schedule(today)
print(schedule.to_summary())

# Confirm no real conflicts in the generated schedule
real_warnings = schedule.detect_conflicts()
if real_warnings:
    for w in real_warnings:
        print(w)
else:
    print("  Conflict check passed — no overlaps in generated schedule.")
