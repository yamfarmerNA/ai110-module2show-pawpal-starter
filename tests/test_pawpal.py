"""
tests/test_pawpal.py — unit tests for PawPal+ core logic.
Run with: python -m pytest
"""

from pawpal_system import Task, Pet, Priority, Frequency, Species


# ---------------------------------------------------------------------------
# Fixtures — reusable objects shared across tests
# ---------------------------------------------------------------------------

def make_task(id=1, title="Morning walk", duration=30,
              priority=Priority.HIGH, frequency=Frequency.DAILY):
    return Task(
        id=id,
        title=title,
        duration_mins=duration,
        priority=priority,
        frequency=frequency,
    )


def make_pet(id=1, name="Mochi"):
    return Pet(id=id, name=name, species=Species.DOG, age=3)


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
