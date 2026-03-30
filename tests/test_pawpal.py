"""
tests/test_pawpal.py — unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

from datetime import date, time, datetime, timedelta

from pawpal_system import (
    Task, Pet, Owner, TimeBlock, Scheduler, Schedule, ScheduledTask,
    Priority, Frequency, Species,
)


# ---------------------------------------------------------------------------
# Fixtures — reusable objects shared across tests
# ---------------------------------------------------------------------------

def make_task(id=1, title="Morning walk", duration=30,
              priority=Priority.HIGH, frequency=Frequency.DAILY,
              preferred_time=None):
    return Task(
        id=id,
        title=title,
        duration_mins=duration,
        priority=priority,
        frequency=frequency,
        preferred_time=preferred_time,
    )


def make_pet(id=1, name="Mochi"):
    return Pet(id=id, name=name, species=Species.DOG, age=3)


def make_scheduler(pets=None):
    """Return a Scheduler with a basic owner and the given pets (default: one empty pet)."""
    owner = Owner(
        id=1,
        name="Jordan",
        available_times=[
            TimeBlock(start=time(8, 0), end=time(10, 0)),
            TimeBlock(start=time(17, 0), end=time(19, 0)),
        ],
    )
    for pet in (pets or [make_pet()]):
        owner.add_pet(pet)
    return Scheduler(owner=owner)


# ---------------------------------------------------------------------------
# Test 1 — Task completion
# ---------------------------------------------------------------------------

def test_mark_complete_sets_flag():
    """Calling mark_complete() should flip is_completed to True."""
    task = make_task()
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_mark_complete_is_idempotent():
    """Calling mark_complete() twice should leave is_completed True."""
    task = make_task()
    task.mark_complete()
    task.mark_complete()

    assert task.is_completed is True


# ---------------------------------------------------------------------------
# Test 2 — Task addition
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = make_pet()
    assert len(pet.tasks) == 0

    pet.add_task(make_task(id=1, title="Walk"))

    assert len(pet.tasks) == 1


def test_add_multiple_tasks_increases_count():
    """Adding three tasks should result in a task count of 3."""
    pet = make_pet()
    pet.add_task(make_task(id=1, title="Walk"))
    pet.add_task(make_task(id=2, title="Feed"))
    pet.add_task(make_task(id=3, title="Groom"))

    assert len(pet.tasks) == 3


# ---------------------------------------------------------------------------
# Test 3 — Edge case: pet with no tasks
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_returns_empty_pending():
    """A pet that has never had tasks added should have an empty pending list."""
    pet = make_pet()
    assert pet.get_pending_tasks() == []


def test_scheduler_with_no_tasks_generates_empty_schedule():
    """Generating a schedule for a pet with no tasks should produce zero scheduled items."""
    pet = make_pet()  # no tasks added
    scheduler = make_scheduler(pets=[pet])
    schedule = scheduler.generate_schedule(date.today())
    assert len(schedule.scheduled_tasks) == 0


# ---------------------------------------------------------------------------
# Test 4 — Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_tasks_by_time_returns_chronological_order():
    """Tasks added out of order should come back sorted earliest preferred_time first."""
    pet = make_pet()
    scheduler = make_scheduler(pets=[pet])

    # Add in reverse chronological order intentionally
    tasks = [
        make_task(id=3, title="Evening feed",  preferred_time=time(17, 30)),
        make_task(id=1, title="Morning walk",  preferred_time=time(8, 0)),
        make_task(id=2, title="Afternoon play", preferred_time=time(14, 0)),
    ]
    sorted_tasks = scheduler.sort_tasks_by_time(tasks)

    assert sorted_tasks[0].preferred_time == time(8, 0)
    assert sorted_tasks[1].preferred_time == time(14, 0)
    assert sorted_tasks[2].preferred_time == time(17, 30)


def test_sort_tasks_by_time_places_no_preferred_time_last():
    """Tasks with no preferred_time should sort after all timed tasks."""
    pet = make_pet()
    scheduler = make_scheduler(pets=[pet])

    tasks = [
        make_task(id=1, title="Grooming",      preferred_time=None),
        make_task(id=2, title="Morning walk",  preferred_time=time(8, 0)),
    ]
    sorted_tasks = scheduler.sort_tasks_by_time(tasks)

    assert sorted_tasks[0].title == "Morning walk"
    assert sorted_tasks[1].title == "Grooming"


# ---------------------------------------------------------------------------
# Test 5 — Filtering
# ---------------------------------------------------------------------------

def test_filter_tasks_by_pet_name():
    """filter_tasks with a pet name should only return that pet's tasks."""
    mochi = make_pet(id=1, name="Mochi")
    luna  = make_pet(id=2, name="Luna")
    mochi.add_task(make_task(id=1, title="Walk"))
    luna.add_task(make_task(id=2, title="Medication"))

    scheduler = make_scheduler(pets=[mochi, luna])
    results = scheduler.filter_tasks(pet_name="Mochi")

    assert all(pet.name == "Mochi" for pet, _ in results)
    assert len(results) == 1


def test_filter_tasks_by_completion_status():
    """filter_tasks(completed=True) should only return finished tasks."""
    pet = make_pet()
    done_task    = make_task(id=1, title="Done task")
    pending_task = make_task(id=2, title="Pending task")
    done_task.mark_complete()
    pet.add_task(done_task)
    pet.add_task(pending_task)

    scheduler = make_scheduler(pets=[pet])

    completed = scheduler.filter_tasks(completed=True)
    pending   = scheduler.filter_tasks(completed=False)

    assert len(completed) == 1 and completed[0][1].title == "Done task"
    assert len(pending)   == 1 and pending[0][1].title   == "Pending task"


# ---------------------------------------------------------------------------
# Test 6 — Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_occurrence():
    """Completing a DAILY task should produce a new task due tomorrow."""
    pet = make_pet()
    task = make_task(id=1, title="Walk", frequency=Frequency.DAILY)
    pet.add_task(task)

    scheduler = make_scheduler(pets=[pet])
    next_task = scheduler.complete_task(pet, task)

    assert task.is_completed is True
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.title == task.title
    assert len(pet.tasks) == 2  # original + new occurrence


def test_complete_weekly_task_creates_next_occurrence():
    """Completing a WEEKLY task should produce a new task due 7 days from now."""
    pet = make_pet()
    task = make_task(id=1, title="Grooming", frequency=Frequency.WEEKLY)
    pet.add_task(task)

    scheduler = make_scheduler(pets=[pet])
    next_task = scheduler.complete_task(pet, task)

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_complete_once_task_creates_no_occurrence():
    """Completing a ONCE task should NOT add a new task — it does not recur."""
    pet = make_pet()
    task = make_task(id=1, title="Vet visit", frequency=Frequency.ONCE)
    pet.add_task(task)

    scheduler = make_scheduler(pets=[pet])
    next_task = scheduler.complete_task(pet, task)

    assert next_task is None
    assert len(pet.tasks) == 1  # no new task added


# ---------------------------------------------------------------------------
# Test 7 — Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_tasks():
    """Two tasks placed at the exact same start time must produce a conflict warning."""
    owner = Owner(id=1, name="Jordan", available_times=[])
    pet   = make_pet()

    t_a = make_task(id=1, title="Bath",         duration=30)
    t_b = make_task(id=2, title="Nail trimming", duration=20)

    overlap_time = datetime.combine(date.today(), time(9, 0))
    schedule = Schedule(date=date.today(), owner=owner)
    schedule.add_scheduled_task(ScheduledTask(task=t_a, pet=pet, scheduled_time=overlap_time))
    schedule.add_scheduled_task(ScheduledTask(task=t_b, pet=pet, scheduled_time=overlap_time))

    warnings = schedule.detect_conflicts()

    assert len(warnings) == 1
    assert "Bath" in warnings[0]
    assert "Nail trimming" in warnings[0]


def test_detect_conflicts_returns_empty_for_sequential_tasks():
    """Tasks that end before the next one starts should produce no warnings."""
    owner = Owner(id=1, name="Jordan", available_times=[])
    pet   = make_pet()

    today = date.today()
    t_a = make_task(id=1, title="Walk",  duration=30)
    t_b = make_task(id=2, title="Feed",  duration=10)

    start_a = datetime.combine(today, time(8, 0))
    start_b = datetime.combine(today, time(8, 30))  # starts exactly when Walk ends

    schedule = Schedule(date=today, owner=owner)
    schedule.add_scheduled_task(ScheduledTask(task=t_a, pet=pet, scheduled_time=start_a))
    schedule.add_scheduled_task(ScheduledTask(task=t_b, pet=pet, scheduled_time=start_b))

    warnings = schedule.detect_conflicts()

    assert warnings == []


def test_generated_schedule_has_no_conflicts():
    """The scheduler's own output should always be conflict-free."""
    pet = make_pet()
    pet.add_task(make_task(id=1, title="Walk",  duration=30, preferred_time=time(8, 0)))
    pet.add_task(make_task(id=2, title="Feed",  duration=10, preferred_time=time(8, 30)))
    pet.add_task(make_task(id=3, title="Groom", duration=20))

    scheduler = make_scheduler(pets=[pet])
    schedule  = scheduler.generate_schedule(date.today())

    assert schedule.detect_conflicts() == []
