# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The data classes model the real-world entities in the app. Owner is the root — it holds a list of Pets and a list of TimeBlocks representing when the owner is free. Each Pet holds a list of Tasks and knows how to filter and sort them by priority. Task captures everything needed to describe a care activity: its duration, Priority (LOW/MEDIUM/HIGH), Frequency (ONCE/DAILY/WEEKLY), and an optional preferred time of day. TimeBlock represents a window of availability and can detect overlaps with other blocks.


- What classes did you include, and what responsibilities did you assign to each?
Data Classes
TimeBlock
Represents a window of time when the owner is available (e.g. 8:00–10:00 AM). Knows how long it is and whether it overlaps with another block. Used by Scheduler to find valid slots for tasks.

Task
A single pet care activity — a walk, feeding, medication, etc. Holds everything needed to describe and schedule it: how long it takes, how urgent it is (Priority), how often it repeats (Frequency), and a preferred time of day. Knows whether it's been done and whether it's overdue.

Pet
An animal owned by the owner. Holds a list of Tasks and can filter/sort them. Its main job is to be a container that groups tasks by animal, so the scheduler knows which pet each task belongs to.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The scheduler places tasks by scanning available TimeBlocks in a fixed 15-minute step (`cursor += timedelta(minutes=15)`) rather than jumping directly to the earliest free slot. This means it could waste up to 14 minutes of availability looking for a gap that is right at a non-aligned boundary, and it never considers reordering tasks to pack them more tightly.

This tradeoff is reasonable for a pet-care scenario because the schedule is meant for a human to follow — clean, aligned time slots (8:00, 8:15, 8:30…) are easier to read and act on than mathematically optimal but awkward times like 8:07 AM. Simplicity in the output matters more than perfect utilization of every minute.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
