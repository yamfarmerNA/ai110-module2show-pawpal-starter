import streamlit as st
from datetime import date, time

# Step 1: Import the classes from pawpal_system so we can use them here
from pawpal_system import (
    Owner, Pet, Task, TimeBlock, Scheduler,
    Priority, Frequency, Species,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Step 2: Manage application "memory" with st.session_state
#
# Streamlit reruns this script from top to bottom on every interaction.
# We store the Owner and Scheduler in st.session_state so they survive
# across reruns — like a vault that stays open while the tab is open.
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
    st.session_state.task_counter = 100  # unique IDs for new tasks

# Convenience references
owner: Owner = st.session_state.owner
pet: Pet = st.session_state.pet
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Owner / Pet info display
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet")
st.write(f"**Owner:** {owner.name}")
st.write(f"**Pet:** {pet.name} ({pet.species.value}, age {pet.age})")

st.divider()

# ---------------------------------------------------------------------------
# Step 3: Add a Task — wired to pet.add_task() with real Task objects
# ---------------------------------------------------------------------------

st.subheader("Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["low", "medium", "high"], index=2)

preferred_time_input = st.time_input("Preferred time (optional)", value=time(8, 0))
use_preferred = st.checkbox("Set a preferred time", value=True)

if st.button("Add task"):
    priority_map = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

    # Increment the counter so every task gets a unique ID
    st.session_state.task_counter += 1

    new_task = Task(
        id=st.session_state.task_counter,
        title=task_title,
        duration_mins=int(duration),
        priority=priority_map[priority_str],
        frequency=Frequency.DAILY,
        preferred_time=preferred_time_input if use_preferred else None,
    )

    # Step 3: call the real method on the Pet object — this updates the
    # pet stored in session_state, so the change persists across reruns
    pet.add_task(new_task)
    st.success(f"Added task: {task_title}")

# Show current tasks
if pet.tasks:
    st.write("**Current tasks:**")
    rows = [
        {
            "Title": t.title,
            "Duration (min)": t.duration_mins,
            "Priority": t.priority.name.capitalize(),
            "Preferred time": t.preferred_time.strftime("%I:%M %p") if t.preferred_time else "—",
            "Done": "✓" if t.is_completed else "",
        }
        for t in pet.tasks
    ]
    st.table(rows)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate Schedule — wired to scheduler.generate_schedule()
# ---------------------------------------------------------------------------

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        schedule = scheduler.generate_schedule(date.today())
        if not schedule.scheduled_tasks:
            st.warning("No tasks could be scheduled. Check that tasks fit within the owner's availability windows.")
        else:
            st.success("Schedule generated!")
            st.text(schedule.to_summary())
