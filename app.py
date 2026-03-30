import streamlit as st
from datetime import date, time

from pawpal_system import (
    Owner, Pet, Task, TimeBlock, Scheduler,
    Priority, Frequency, Species,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state — persists across reruns
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        id=1,
        name="Jordan",
        available_times=[
            TimeBlock(start=time(8, 0),  end=time(10, 0)),
            TimeBlock(start=time(17, 0), end=time(19, 0)),
        ],
    )

if "pet" not in st.session_state:
    st.session_state.pet = Pet(id=1, name="Mochi", species=Species.DOG, age=3)
    st.session_state.owner.add_pet(st.session_state.pet)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 100

owner: Owner     = st.session_state.owner
pet: Pet         = st.session_state.pet
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Owner & Pet header
# ---------------------------------------------------------------------------

col_a, col_b, col_c = st.columns(3)
col_a.metric("Owner", owner.name)
col_b.metric("Pet", pet.name)
col_c.metric("Species / Age", f"{pet.species.value.capitalize()}, {pet.age} yrs")

st.divider()

# ---------------------------------------------------------------------------
# Add a Task
# ---------------------------------------------------------------------------

st.subheader("Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns([1, 2])
with col4:
    use_preferred = st.checkbox("Set preferred time", value=True)
with col5:
    preferred_time_input = st.time_input("Preferred time", value=time(8, 0),
                                         disabled=not use_preferred)

if st.button("Add task", type="primary"):
    priority_map = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
    st.session_state.task_counter += 1

    new_task = Task(
        id=st.session_state.task_counter,
        title=task_title,
        duration_mins=int(duration),
        priority=priority_map[priority_str],
        frequency=Frequency.DAILY,
        preferred_time=preferred_time_input if use_preferred else None,
    )
    pet.add_task(new_task)
    st.success(f"Added **{task_title}** ({priority_str} priority, {int(duration)} min)")

st.divider()

# ---------------------------------------------------------------------------
# Task List — sorted by preferred time, filtered by status
# ---------------------------------------------------------------------------

st.subheader("Task List")

# Filter control
status_choice = st.radio("Show", ["Pending", "Completed", "All"], horizontal=True)
completed_filter = {"Pending": False, "Completed": True, "All": None}[status_choice]

# Use Scheduler methods: filter_tasks() then sort_tasks_by_time()
pairs = scheduler.filter_tasks(pet_name=pet.name, completed=completed_filter)
sorted_tasks = scheduler.sort_tasks_by_time([t for _, t in pairs])

if sorted_tasks:
    PRIORITY_ICON = {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}
    rows = [
        {
            "Title": t.title,
            "Priority": f"{PRIORITY_ICON[t.priority]} {t.priority.name.capitalize()}",
            "Duration": f"{t.duration_mins} min",
            "Preferred time": t.preferred_time.strftime("%I:%M %p") if t.preferred_time else "—",
            "Status": "✅ Done" if t.is_completed else "⏳ Pending",
        }
        for t in sorted_tasks
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption(f"Sorted by preferred time · {len(sorted_tasks)} task(s) shown")
else:
    if status_choice == "Pending":
        st.success("All tasks are complete — nothing left to do!")
    elif status_choice == "Completed":
        st.info("No completed tasks yet.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Mark a Task Complete
# ---------------------------------------------------------------------------

pending_pairs = scheduler.filter_tasks(pet_name=pet.name, completed=False)
pending_tasks = [t for _, t in pending_pairs]

if pending_tasks:
    st.subheader("Mark a Task Complete")
    task_options = {t.title: t for t in pending_tasks}
    chosen_title = st.selectbox("Select task", list(task_options.keys()))

    if st.button("Mark complete"):
        chosen_task = task_options[chosen_title]
        next_task = scheduler.complete_task(pet, chosen_task)
        st.success(f"**{chosen_task.title}** marked as complete!")
        if next_task:
            st.info(
                f"This is a **{chosen_task.frequency.value}** task — next occurrence added "
                f"for **{next_task.due_date.strftime('%A, %B %d')}**."
            )

    st.divider()

# ---------------------------------------------------------------------------
# Generate Today's Schedule
# ---------------------------------------------------------------------------

st.subheader("Today's Schedule")

if st.button("Generate schedule", type="primary"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        schedule = scheduler.generate_schedule(date.today())

        # --- Conflict warnings: surface before the table so they're seen first ---
        conflicts = schedule.detect_conflicts()
        if conflicts:
            st.error(
                f"**{len(conflicts)} scheduling conflict(s) detected.** "
                "Review the warnings below and adjust task times or durations."
            )
            for warning in conflicts:
                # Parse out the key info and present it as an actionable callout
                st.warning(f"⚠️ {warning}")
            st.caption(
                "Tip: shorten a task's duration or change its preferred time "
                "to resolve the overlap."
            )
        else:
            st.success("No conflicts — your schedule is clean!")

        # --- Schedule table ---
        if not schedule.scheduled_tasks:
            st.warning(
                "No tasks could be placed. Check that task durations fit within "
                "the owner's availability windows (8–10 AM and 5–7 PM)."
            )
        else:
            PRIORITY_ICON = {Priority.HIGH: "🔴", Priority.MEDIUM: "🟡", Priority.LOW: "🟢"}
            rows = []
            for st_task in schedule.get_tasks_by_time():
                rows.append({
                    "Time": st_task.scheduled_time.strftime("%I:%M %p"),
                    "Ends": st_task.end_time.strftime("%I:%M %p"),
                    "Task": st_task.task.title,
                    "Pet": st_task.pet.name,
                    "Priority": f"{PRIORITY_ICON[st_task.task.priority]} {st_task.task.priority.name.capitalize()}",
                    "Why": st_task.reason,
                })

            st.dataframe(rows, hide_index=True, use_container_width=True)
            st.caption(
                f"{date.today().strftime('%A, %B %d %Y')} · "
                f"{len(schedule.scheduled_tasks)} task(s) scheduled for {owner.name}"
            )
