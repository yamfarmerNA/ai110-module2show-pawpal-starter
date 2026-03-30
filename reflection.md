# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

I basically started with the real-world things a pet owner actually deals with — the owner, their pets, and the tasks those pets need done. Owner sits at the top and holds everything else. Each Pet has a list of Tasks, and Tasks know stuff like how long they take, how urgent they are, and whether they've been done. TimeBlock was kind of a utility class to represent when the owner is actually free.

- What classes did you include, and what responsibilities did you assign to each?

Owner handles the pets and the availability windows. Pet is mostly a container that groups tasks by animal. Task holds all the details about one care activity. TimeBlock represents a chunk of free time and can check if it overlaps with another. Scheduler is the brain that actually figures out what goes where. Schedule is just the finished result — the day's plan with all the reasoning attached.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yeah it changed more than I expected once I got into the code. The biggest thing was adding `due_date` to Task — I didn't think I'd need it until I built the recurring task feature and realized there was no way to say "this task is due tomorrow." I also added three methods to Scheduler (`sort_tasks_by_time`, `filter_tasks`, `complete_task`) that weren't in my original plan at all. They came up naturally when I started building the UI and realized the app needed to slice data in ways I hadn't thought about up front.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler looks at three things: the owner's available time windows, each task's priority, and whether the task has a preferred time of day. Priority ended up being the most important one because that's what controls which tasks compete for slots first — HIGH always goes before LOW, and overdue tasks get a bonus score on top of that. Preferred time is more of a soft preference; if 8 AM is already taken the task just slides to the next open slot. Time windows are the hard limit — if a task doesn't fit inside any window, it just doesn't get scheduled that day.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler places tasks by scanning available TimeBlocks in a fixed 15-minute step (`cursor += timedelta(minutes=15)`) rather than jumping directly to the earliest free slot. This means it could waste up to 14 minutes of availability looking for a gap that is right at a non-aligned boundary, and it never considers reordering tasks to pack them more tightly.

This tradeoff is reasonable for a pet-care scenario because the schedule is meant for a human to follow — clean, aligned time slots (8:00, 8:15, 8:30…) are easier to read and act on than mathematically optimal but awkward times like 8:07 AM. Simplicity in the output matters more than perfect utilization of every minute.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI was useful in pretty much every phase — brainstorming the class structure at the start, filling in method logic once the stubs were written, and coming up with test cases for edge cases I hadn't thought of like a pet with zero tasks. The prompts that worked best were specific ones like "given this method, what edge cases should I test?" — broad prompts like "write me a scheduler" just gave generic answers. Asking the AI to explain what it suggested before I accepted it also helped me actually understand the code instead of just pasting it in.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

At one point AI suggested using a set to track scheduled times for conflict detection, simpler code, but it would only catch exact-same-start-time collisions and miss cases where one task starts in the middle of another. I went with the interval-overlap check (`a.start < b.end and b.start < a.end`) instead because I could actually reason through why it handles every overlap case. Then I wrote `test_detect_conflicts_flags_overlapping_tasks` to confirm it before moving on.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The suite covers 16 tests — task completion, adding tasks, sorting by time, filtering by name and status, recurring task creation, and conflict detection. The recurrence and conflict tests were probably the most important ones because those are the behaviors a user would actually notice if they broke. Confirming that `ONCE` tasks don't accidentally create a next occurrence, and that back-to-back tasks don't trigger a false conflict warning, made me a lot more confident in the edge cases.

**b. Confidence**

- How confident are you that your 
Relatively confident
- What edge cases would you test next if you had more time?

Pretty confident in the core logic, everything I could think to test passes, and the generated schedule even runs `detect_conflicts()` on itself to verify it came out clean. The main gap is the UI side since none of the tests actually simulate button clicks or session state. If I had more time I'd test what happens when all available time slots are completely full, and whether the scheduler slows down noticeably with a lot of tasks.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Honestly the Scheduler class. It started as just one method and ended up with a whole set of tools that all fit together, sort, filter, complete, detect conflicts. None of it felt like I was adding stuff just to add it, every method solved something that actually came up during the build. Getting 16/16 on the first full test run was a nice bonus too.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

The biggest thing is multiple pets in the UI, right now it's hardcoded to one pet, so if you want a second one you have to go into the code. I'd also make recurring tasks actually persist somewhere instead of just living in memory, because right now everything resets when you refresh the page which kind of defeats the purpose of tracking daily tasks.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Drawing out the UML first, even roughly, saved a ton of time because I wasn't trying to figure out structure and logic at the same time when writing code. With AI, I learned that treating it like a teammate to think through problems with works way better than using it as a copy-paste machine. Specific questions get useful answers, vague ones don't.
