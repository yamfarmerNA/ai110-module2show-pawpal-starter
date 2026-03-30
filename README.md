# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The suite covers 16 tests across 7 areas:

| Area | What it checks |
|---|---|
| Task completion | `mark_complete()` sets the flag; calling it twice is safe |
| Task addition | `add_task()` correctly grows the pet's task list |
| Edge cases | Pet with no tasks returns empty lists; scheduler produces an empty schedule |
| Sorting | `sort_tasks_by_time()` returns tasks in chronological order; tasks with no preferred time sort last |
| Filtering | `filter_tasks()` correctly isolates by pet name and by completion status |
| Recurrence | Completing a DAILY task creates a new occurrence due tomorrow; WEEKLY tasks due in 7 days; ONCE tasks produce no new occurrence |
| Conflict detection | Overlapping tasks produce a warning string; back-to-back tasks and scheduler output are conflict-free |

**Confidence level: ★★★★☆**
Core scheduling behaviors (sorting, filtering, recurrence, conflict detection) are verified end-to-end. The main untested area is the Streamlit UI layer and multi-week recurring reset logic, which would require integration or browser-level tests.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
