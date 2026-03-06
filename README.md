# To-Do List and Calendar Scheduler


### Prompt 1
**Exact Prompt**: "Write a program in python with a split functionality that allows me to make a to do list and also calander function that lets me add my schedule and my appointments and meetings similar to the website monday.com & trello basically putting the Schedule and meeting planner from monday.com and the to do list from trello together into one program"

**Intention**: Request to create a Python program with a GUI that combines a to-do list (like Trello) and a calendar scheduler (like Monday.com) in a split interface.

**Actual Result**: Created `todo_calendar.py` with a tabbed Tkinter interface, including to-do list management (add, mark done, remove tasks) and calendar functionality (add/remove events per date), plus `requirements.txt` and basic `README.md`.

### Prompt 2
**Exact Prompt**: "Also add a full documentation of all prompts, their intentions and the ACTUAL result in the readme."

**Intention**: Enhance the README with detailed documentation of all user interface elements (referred to as "prompts"), including their purposes and outcomes.

**Actual Result**: Updated `README.md` with comprehensive descriptions of each UI component, their intentions, and actual results in the Usage section.

### Prompt 3
**Exact Prompt**: "I need my EXACT prompts documented. EVERYTIME i give you a prompt. Now redo the readme with my EXACT prompts since the beginning"

**Intention**: Document the exact text of all user prompts from the conversation start, and redo the README to include this information.

**Actual Result**: Added a new "User Prompts Documentation" section to `README.md` listing each prompt verbatim, along with intentions and results.

### Prompt 4
**Exact Prompt**: "Please add a visual upgrade. This app looks very bare bones. Keep it futuristic but user friendly. Additionally add the Events for a selected date to the calendar so it is actually shown on the calendar what events are on what day. Also make the calendar bigger, focus more on weekly (let me go through the weeks like pages) and add times so I can add my meetings to specific times on the specific day. Make it create a block that shows from what to what time it is. Kind of like a graph where the X achses is the days and the y achses is the time"

**Intention**: Upgrade the UI to a futuristic dark theme, integrate events visually on the calendar, switch to a weekly grid view with time slots, allow navigation through weeks, and display events as time-based blocks.

**Actual Result**: Updated the app with a dark futuristic UI (black backgrounds, colored buttons, white text), replaced the simple calendar with a monthly selector and a weekly canvas grid showing time slots (8 AM - 8 PM), events as cyan blocks with text, navigation buttons for weeks, and input fields for event times. Window size increased to 1200x800. Updated README accordingly.

### Prompt 5
**Exact Prompt**: "Also add the ability to let me "check" my tasks that let me show that its finished. Make an unfinished task red and a finished task green"

**Intention**: Add a visual check feature for tasks, displaying unfinished tasks in red and finished tasks in green.

**Actual Result**: Replaced the listbox with a Treeview widget that displays tasks in red for unfinished and green for finished. Added a "Toggle Done" button to switch the status of selected tasks. Updated the UI styling for a consistent dark theme.

### Prompt 6
**Exact Prompt**: "make a clickable box next to the task instead of having to click it at the bottom"

**Intention**: Replace the bottom button for toggling task status with clickable checkboxes directly next to each task.

**Actual Result**: Implemented checkboxes next to each task for immediate toggling between unfinished (red) and finished (green) states, and added per-task remove buttons ('x').

### Prompt 7
**Exact Prompt**: "Please completely remake the visual. I want it to look more bubbly not cornered and also I want it to be a white background. I want it to look less like a shitty program and more like a full fledged professional tool"

**Intention**: Completely redesign the UI to a clean, professional white theme with raised buttons and borders for a "bubbly" feel, making it look like a professional tool.

**Actual Result**: Switched to a white background theme with black text, light blue accents, raised buttons, bordered frames, and updated colors throughout for a clean, professional appearance.

### Prompt 8
**Exact Prompt**: "Give me the ability to click on the calendar to add the event directly through a pop up window that opens when i click on monday 8 am that lets me add the task directly"

**Intention**: Enable direct event creation by clicking on specific time slots in the weekly calendar grid, opening a popup to quickly add events without using the bottom input fields.

**Actual Result**: Implemented clickable time slots in the weekly grid that trigger a popup window showing the selected date and time, with pre-filled start time and default end time, allowing users to enter event details and save directly from the popup.

### Prompt 9
**Exact Prompt**: "I get this error: ... AttributeError: '_tkinter.tkapp' object has no attribute 'add_event'"

**Intention**: Fix the missing `add_event` method that was accidentally removed when implementing the popup feature, causing the app to crash.

**Actual Result**: Restored the `add_event` method to support the traditional bottom input field method for adding events, while keeping the new popup feature. Both methods now work together.

### Prompt 10
**Exact Prompt**: "When the pop up opens, let me just simply press enter to close it and add the event to the correct time slot. Additionally give me the option to click on it again and press backspace to remove it again"

**Intention**: Add keyboard shortcuts for faster event management - Enter to save/close popup and right-click to delete events directly from the calendar.

**Actual Result**: Added Enter key binding to the popup to save events instantly, and implemented right-click functionality on events to delete them. Event blocks are now tagged with indices for easy deletion.

### Prompt 11
**Exact Prompt**: "make sure when the event is added, it still shows the time. Additionally give the user a short pop up when opening the program to explain the controls of the calendar & schedule and on the To-Do List. Also add a splash screen that fakes "loading" when the program starts"

**Intention**: Enhance user experience with visual feedback (show event times), help documentation on startup, and a professional loading splash screen.

**Actual Result**: Added event time display on calendar blocks (showing start-end times), created a loading splash screen with animated progress bar, and implemented a help popup with controls guide for both tabs that appears on first launch.