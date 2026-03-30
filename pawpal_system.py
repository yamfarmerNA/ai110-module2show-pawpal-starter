"""
PawPal+ — core system classes.

Design order:
  1. Enums (Priority, Frequency, Species)
  2. Task
  3. Pet
  4. TimeBlock
  5. Owner
  6. ScheduledTask + Schedule
  7. Scheduler  ← main logic lives here
"""


from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class Species(Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    OTHER = "other"


# ---------------------------------------------------------------------------
# TimeBlock — a window of availability (e.g. 8:00–10:00)
# ---------------------------------------------------------------------------

@dataclass
class TimeBlock:
    start: time
    end: time

    def duration_mins(self) -> int:
        """Return the length of this block in minutes."""
        start_dt = datetime.combine(date.today(), self.start)
        end_dt   = datetime.combine(date.today(), self.end)
        return int((end_dt - start_dt).total_seconds() // 60)

    def overlaps(self, other: TimeBlock) -> bool:
        """Return True if this block overlaps with another."""
        return self.start < other.end and other.start < self.end


# ---------------------------------------------------------------------------
# Task — a single pet care activity
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    title: str
    duration_mins: int
    priority: Priority
    frequency: Frequency
    preferred_time: Optional[time] = None   # e.g. time(8, 0) means "prefer 8 AM"
    is_completed: bool = False
    due_date: Optional[date] = None          # set automatically for recurring next occurrences

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

    def is_overdue(self, reference: datetime) -> bool:
        """Return True if preferred_time has passed and the task is incomplete."""
        if self.preferred_time is None:
            return False
        deadline = datetime.combine(reference.date(), self.preferred_time)
        return reference > deadline and not self.is_completed


# ---------------------------------------------------------------------------
# Pet — an animal with a list of care tasks
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    id: int
    name: str
    species: Species
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return [t for t in self.tasks if not t.is_completed]

    def get_tasks_by_priority(self) -> list[Task]:
        """Return pending tasks sorted highest priority first."""
        return sorted(self.get_pending_tasks(), key=lambda t: t.priority.value, reverse=True)


# ---------------------------------------------------------------------------
# Owner — the person managing one or more pets
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    id: int
    name: str
    available_times: list[TimeBlock] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        return self.pets


# ---------------------------------------------------------------------------
# ScheduledTask — a Task placed at a specific time on the calendar
# ---------------------------------------------------------------------------

@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    scheduled_time: datetime
    reason: str = ""

    @property
    def end_time(self) -> datetime:
        """Compute when this task ends based on duration."""
        return self.scheduled_time + timedelta(minutes=self.task.duration_mins)


# ---------------------------------------------------------------------------
# Schedule — the finished daily plan for one owner
# ---------------------------------------------------------------------------

@dataclass
class Schedule:
    date: date
    owner: Owner
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)

    def add_scheduled_task(self, st: ScheduledTask) -> None:
        """Append a scheduled task and record its reason in explanations."""
        self.scheduled_tasks.append(st)
        if st.reason:
            self.explanations.append(st.reason)

    def get_tasks_by_time(self) -> list[ScheduledTask]:
        """Return scheduled tasks sorted by start time."""
        return sorted(self.scheduled_tasks, key=lambda st: st.scheduled_time)

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for any tasks whose time windows overlap."""
        warnings = []
        ordered = self.get_tasks_by_time()
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:]:
                if a.scheduled_time < b.end_time and b.scheduled_time < a.end_time:
                    warnings.append(
                        f"WARNING: '{a.task.title}' ({a.pet.name}) "
                        f"{a.scheduled_time.strftime('%I:%M %p')}–{a.end_time.strftime('%I:%M %p')} "
                        f"overlaps '{b.task.title}' ({b.pet.name}) "
                        f"{b.scheduled_time.strftime('%I:%M %p')}–{b.end_time.strftime('%I:%M %p')}"
                    )
        return warnings

    def to_summary(self) -> str:
        """Return a human-readable summary of the schedule."""
        lines = [
            f"Today's Schedule -- {self.date.strftime('%A, %B %d %Y')}",
            f"Owner : {self.owner.name}",
            "-" * 50,
        ]
        for st in self.get_tasks_by_time():
            start = st.scheduled_time.strftime("%I:%M %p")
            end   = st.end_time.strftime("%I:%M %p")
            pri   = st.task.priority.name.capitalize()
            lines.append(
                f"  {start} - {end}  |  [{pri}]  {st.task.title}  ({st.pet.name})"
            )
            if st.reason:
                lines.append(f"              ->  {st.reason}")
        lines.append("-" * 50)
        lines.append(f"  {len(self.scheduled_tasks)} task(s) scheduled")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler — the brain that produces a Schedule
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self._last_generated: Optional[date] = None

    def generate_schedule(self, target_date: date) -> Schedule:
        """Build and return a conflict-free Schedule for the given date."""
        if self._last_generated != target_date:
            self.generate_recurring_tasks()
            self._last_generated = target_date

        schedule = Schedule(date=target_date, owner=self.owner)

        # Gather (pet, task) pairs sorted by score descending
        candidates = sorted(
            self.get_upcoming_tasks(),
            key=lambda pair: self._score_task(pair[1], target_date),
            reverse=True,
        )

        # Cursor tracks current placement time within each TimeBlock
        for pet, task in candidates:
            slot = self._find_slot(task, target_date, schedule)
            if slot is None:
                continue  # no room today — skip
            reason = self._explain_decision(task, pet, slot)
            schedule.add_scheduled_task(ScheduledTask(
                task=task,
                pet=pet,
                scheduled_time=slot,
                reason=reason,
            ))

        return schedule

    def check_conflicts(self, task: Task, start_time: datetime, schedule: Schedule) -> bool:
        """Return True if placing task at start_time overlaps an existing scheduled task."""
        end_time = start_time + timedelta(minutes=task.duration_mins)
        for st in schedule.scheduled_tasks:
            if start_time < st.end_time and st.scheduled_time < end_time:
                return True
        return False

    def get_upcoming_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all incomplete (pet, task) pairs across all pets, sorted by priority."""
        pairs = [
            (pet, task)
            for pet in self.owner.get_pets()
            for task in pet.get_tasks_by_priority()
        ]
        return pairs

    def sort_tasks_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by preferred_time (tasks with no time go last)."""
        return sorted(tasks, key=lambda t: t.preferred_time or time(23, 59))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Return (pet, task) pairs filtered by pet name and/or completion status.
        Pass pet_name="Mochi" to see only Mochi's tasks.
        Pass completed=False to see only pending tasks.
        """
        results = []
        for pet in self.owner.get_pets():
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.is_completed != completed:
                    continue
                results.append((pet, task))
        return results

    def complete_task(self, pet: Pet, task: Task) -> Optional[Task]:
        """
        Mark task complete and, for DAILY/WEEKLY tasks, automatically add a new
        Task instance to the pet for the next occurrence using timedelta.
        Returns the new Task if one was created, otherwise None.
        """
        task.mark_complete()

        today = date.today()
        if task.frequency == Frequency.DAILY:
            next_due = today + timedelta(days=1)
        elif task.frequency == Frequency.WEEKLY:
            next_due = today + timedelta(weeks=1)
        else:
            return None  # ONCE tasks don't recur

        # Generate a unique ID by taking the max existing id + 1
        all_ids = [t.id for p in self.owner.get_pets() for t in p.tasks]
        next_id = max(all_ids) + 1 if all_ids else 1

        next_task = Task(
            id=next_id,
            title=task.title,
            duration_mins=task.duration_mins,
            priority=task.priority,
            frequency=task.frequency,
            preferred_time=task.preferred_time,
            due_date=next_due,
        )
        pet.add_task(next_task)
        return next_task

    def generate_recurring_tasks(self) -> None:
        """Reset completed DAILY tasks each day and WEEKLY tasks each Monday."""
        today = date.today()
        for pet in self.owner.get_pets():
            for task in pet.tasks:
                if task.frequency == Frequency.DAILY and task.is_completed:
                    task.is_completed = False
                elif task.frequency == Frequency.WEEKLY and task.is_completed:
                    # Reset on Monday (weekday 0) or if no preferred_time set
                    if today.weekday() == 0:
                        task.is_completed = False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _score_task(self, task: Task, target_date: date) -> int:
        """Return a scheduling score: priority value plus +2 bonus if overdue."""
        score = task.priority.value
        reference = datetime.combine(target_date, time(12, 0))
        if task.is_overdue(reference):
            score += 2
        return score

    def _explain_decision(self, task: Task, pet: Pet, scheduled_time: datetime) -> str:
        """Return a one-sentence reason for this scheduling decision."""
        pri = task.priority.name.capitalize()
        t   = scheduled_time.strftime("%I:%M %p")
        if task.preferred_time:
            pref = task.preferred_time.strftime("%I:%M %p")
            return f"{pri} priority -- preferred {pref}, scheduled {t} for {pet.name}."
        return f"{pri} priority task for {pet.name}, placed at earliest available slot ({t})."

    def _find_slot(self, task: Task, target_date: date, schedule: Schedule) -> Optional[datetime]:
        """Return the earliest conflict-free datetime for task, or None if no slot fits."""
        for block in self.owner.available_times:
            cursor = datetime.combine(target_date, block.start)
            block_end = datetime.combine(target_date, block.end)

            while cursor + timedelta(minutes=task.duration_mins) <= block_end:
                if not self.check_conflicts(task, cursor, schedule):
                    return cursor
                # Advance past the conflicting task
                cursor += timedelta(minutes=15)  # step in 15-min increments

        return None


# ---------------------------------------------------------------------------
# Sample data loader — useful for manual testing and the Streamlit demo
# ---------------------------------------------------------------------------

def load_sample_data() -> Scheduler:
    """Return a Scheduler pre-populated with a sample owner, two pets, and tasks."""
    owner = Owner(id=1, name="Jordan", available_times=[
        TimeBlock(start=time(8, 0),  end=time(10, 0)),
        TimeBlock(start=time(17, 0), end=time(19, 0)),
    ])

    mochi = Pet(id=1, name="Mochi", species=Species.DOG, age=3)
    mochi.add_task(Task(
        id=1, title="Morning walk",
        duration_mins=30, priority=Priority.HIGH,
        frequency=Frequency.DAILY, preferred_time=time(8, 0),
    ))
    mochi.add_task(Task(
        id=2, title="Feeding",
        duration_mins=10, priority=Priority.HIGH,
        frequency=Frequency.DAILY,
    ))
    mochi.add_task(Task(
        id=3, title="Grooming",
        duration_mins=20, priority=Priority.LOW,
        frequency=Frequency.WEEKLY,
    ))

    owner.add_pet(mochi)
    return Scheduler(owner)
