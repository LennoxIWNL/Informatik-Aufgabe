import tkinter as tk
import tkinter.ttk as ttk
from tkcalendar import Calendar
import json
from datetime import datetime, timedelta
import tkinter.messagebox
import time

class TodoCalendarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Professional To-Do & Calendar Scheduler")
        self.geometry("1400x900")
        self.config(bg='white')

        # Show splash screen
        self.show_splash_screen()

        # Style for light, professional theme
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', background='white', foreground='black', fieldbackground='white')
        style.map('Treeview', background=[('selected', 'lightblue')])
        style.configure('TNotebook', background='white')
        style.configure('TNotebook.Tab', background='lightgray', foreground='black')
        style.map('TNotebook.Tab', background=[('selected', 'white')])
        style.configure('TButton', relief='raised', borderwidth=2)
        style.configure('TLabel', background='white', foreground='black')
        style.configure('TEntry', fieldbackground='white')

        # Data structures
        self.tasks = []  # List of dicts: {'task': str, 'done': bool}
        self.events = {}  # Dict: date_str -> list of {'event': str, 'start': str, 'end': str}

        # Load data
        self.load_data()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # To-Do List Tab
        self.todo_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.todo_frame, text="To-Do List")
        self.setup_todo_tab()

        # Calendar Tab
        self.cal_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.cal_frame, text="Calendar & Schedule")
        self.setup_calendar_tab()

        # Bind close event to save data
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Show help popup after window is drawn
        self.after(500, self.show_help_popup)

    def show_splash_screen(self):
        """Show a loading splash screen"""
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.geometry("400x200")
        splash.config(bg='white')
        
        # Center splash screen
        splash.update_idletasks()
        x = (splash.winfo_screenwidth() - 400) // 2
        y = (splash.winfo_screenheight() - 200) // 2
        splash.geometry(f"400x200+{x}+{y}")
        
        tk.Label(splash, text="Professional To-Do & Calendar", bg='white', fg='black', font=('Arial', 16, 'bold')).pack(pady=20)
        tk.Label(splash, text="Loading...", bg='white', fg='gray', font=('Arial', 12)).pack(pady=10)
        
        progress = tk.Canvas(splash, bg='white', height=10, highlightthickness=0)
        progress.pack(pady=20, padx=50, fill=tk.X)
        
        # Simulate loading
        for i in range(0, 101, 10):
            progress.delete("all")
            progress.create_rectangle(0, 0, (i / 100) * 300, 10, fill='lightblue', outline='black')
            progress.update()
            time.sleep(0.05)
        
        splash.destroy()

    def show_help_popup(self):
        """Show help popup with controls"""
        help_window = tk.Toplevel(self)
        help_window.title("Quick Guide")
        help_window.geometry("500x400")
        help_window.config(bg='white')
        
        text = tk.Text(help_window, bg='white', fg='black', font=('Arial', 10), wrap=tk.WORD, relief='flat')
        text.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        help_text = """📋 TO-DO LIST CONTROLS:
✓ Click checkbox to mark task as done
✗ Click × button to remove task
• Red text = Unfinished, Green text = Finished
• Add new tasks in the input field

📅 CALENDAR & SCHEDULE CONTROLS:
• Click on any time slot to add an event
• Press ENTER in popup to save quickly
• Right-click events to delete them
• Use ◀ ▶ buttons to navigate weeks
• Events display with start time

💡 TIPS:
• Data auto-saves when you close
• Click calendar date to jump to that week
• Times are in 24-hour format (HH:MM)
"""
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
        tk.Button(help_window, text="Got it!", command=help_window.destroy, bg='lightblue', fg='black', relief='raised', borderwidth=1).pack(pady=10)

    def setup_todo_tab(self):
        # Task list display
        self.task_frame = tk.Frame(self.todo_frame, bg='white')
        self.task_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Input frame
        input_frame = tk.Frame(self.todo_frame, bg='white')
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(input_frame, text="New Task:", fg='black', bg='white').pack(side=tk.LEFT)
        self.task_entry = tk.Entry(input_frame, bg='white', fg='black', insertbackground='black')
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Buttons frame
        btn_frame = tk.Frame(self.todo_frame, bg='white')
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(btn_frame, text="Add Task", command=self.add_task, bg='lightblue', fg='black', relief='raised', borderwidth=2).pack(side=tk.LEFT)

        # Initial update
        self.update_todo_list()

    def setup_calendar_tab(self):
        # Times and days
        self.times = [f"{h:02d}:00" for h in range(8, 21)]  # 8:00 to 20:00
        self.days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())

        # Monthly calendar for selection
        self.calendar = Calendar(self.cal_frame, selectmode='day', date_pattern='y-mm-dd', background='white', foreground='black', selectbackground='lightblue', selectforeground='black')
        self.calendar.pack(fill=tk.X, padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", self.on_date_select)

        # Weekly view frame
        self.week_frame = tk.Frame(self.cal_frame, bg='white')
        self.week_frame.pack(fill=tk.BOTH, expand=True)

        # Navigation
        nav_frame = tk.Frame(self.week_frame, bg='white')
        nav_frame.pack(fill=tk.X)
        self.prev_btn = tk.Button(nav_frame, text="◀", command=self.prev_week, bg='lightgray', fg='black', relief='raised', borderwidth=1, font=('Arial', 12))
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.week_label = tk.Label(nav_frame, text="", fg='black', bg='white', font=('Arial', 12, 'bold'))
        self.week_label.pack(side=tk.LEFT, expand=True)
        self.next_btn = tk.Button(nav_frame, text="▶", command=self.next_week, bg='lightgray', fg='black', relief='raised', borderwidth=1, font=('Arial', 12))
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # Canvas for grid
        self.canvas = tk.Canvas(self.week_frame, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.update_week_label()
        self.draw_week()

        # Input frame for events
        event_input_frame = tk.Frame(self.cal_frame, bg='white')
        event_input_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(event_input_frame, text="Event:", fg='black', bg='white').pack(side=tk.LEFT)
        self.event_entry = tk.Entry(event_input_frame, bg='white', fg='black', insertbackground='black')
        self.event_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        tk.Label(event_input_frame, text="Start (HH:MM):", fg='black', bg='white').pack(side=tk.LEFT)
        self.start_entry = tk.Entry(event_input_frame, width=10, bg='white', fg='black', insertbackground='black')
        self.start_entry.pack(side=tk.LEFT)
        tk.Label(event_input_frame, text="End (HH:MM):", fg='black', bg='white').pack(side=tk.LEFT)
        self.end_entry = tk.Entry(event_input_frame, width=10, bg='white', fg='black', insertbackground='black')
        self.end_entry.pack(side=tk.LEFT)
        tk.Button(event_input_frame, text="Add Event", command=self.add_event, bg='lightblue', fg='black', relief='raised', borderwidth=1).pack(side=tk.LEFT, padx=(5, 0))

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            self.tasks.append({'task': task_text, 'done': False})
            self.update_todo_list()
            self.task_entry.delete(0, tk.END)

    def update_todo_list(self):
        # Clear existing frames
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        # Add task frames
        for task in self.tasks:
            frame = tk.Frame(self.task_frame, bg='white', relief='ridge', borderwidth=1)
            var = tk.BooleanVar(value=task['done'])
            cb = tk.Checkbutton(frame, variable=var, command=lambda t=task, v=var, l=None: self.toggle_task(t, v, l), bg='white', activebackground='white', selectcolor='lightblue')
            label = tk.Label(frame, text=task['task'], fg='red' if not task['done'] else 'green', bg='white', font=('Arial', 10))
            remove_btn = tk.Button(frame, text='×', command=lambda t=task: self.remove_single_task(t), bg='lightcoral', fg='black', relief='raised', borderwidth=1, width=2, font=('Arial', 10, 'bold'))
            cb.pack(side=tk.LEFT, padx=5)
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            remove_btn.pack(side=tk.RIGHT, padx=5)
            frame.pack(fill=tk.X, pady=5, padx=10)
            # Store label for updating color
            task['label'] = label

    def toggle_task(self, task, var, label):
        task['done'] = var.get()
        task['label'].config(fg='green' if task['done'] else 'red')

    def remove_single_task(self, task):
        self.tasks.remove(task)
        self.update_todo_list()

    def on_date_select(self, event):
        date_str = self.calendar.get_date()
        selected_date = datetime.strptime(date_str, '%Y-%m-%d')
        self.current_week_start = selected_date - timedelta(days=selected_date.weekday())
        self.update_week_label()
        self.draw_week()

    def prev_week(self):
        self.current_week_start -= timedelta(days=7)
        self.update_week_label()
        self.draw_week()

    def next_week(self):
        self.current_week_start += timedelta(days=7)
        self.update_week_label()
        self.draw_week()

    def update_week_label(self):
        end = self.current_week_start + timedelta(days=6)
        self.week_label.config(text=f"Week of {self.current_week_start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

    def draw_week(self):
        self.canvas.delete('all')
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1:
            width = 1200
        if height <= 1:
            height = 700
        day_width = width / 7
        time_height = height / len(self.times)
        # Draw day headers
        for i, day in enumerate(self.days):
            x = i * day_width
            self.canvas.create_text(x + day_width / 2, 20, text=day, fill='black', font=('Arial', 12, 'bold'))
        # Draw time labels
        for i, time in enumerate(self.times):
            y = 40 + i * time_height
            self.canvas.create_text(10, y + time_height / 2, text=time, fill='black', anchor='w')
        # Draw horizontal lines
        for i in range(len(self.times) + 1):
            y = 40 + i * time_height
            self.canvas.create_line(0, y, width, y, fill='lightgray')
        # Draw vertical lines
        for i in range(8):
            x = i * day_width
            self.canvas.create_line(x, 0, x, height, fill='lightgray')
        # Draw clickable time slots
        for d in range(7):
            for t in range(len(self.times)):
                x1 = d * day_width + 50
                y1 = 40 + t * time_height
                x2 = (d + 1) * day_width
                y2 = y1 + time_height
                date = (self.current_week_start + timedelta(days=d)).strftime('%Y-%m-%d')
                time_str = self.times[t]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill='', outline='', tags=f"slot_{d}_{t}_{date}_{time_str}")
                self.canvas.tag_bind(f"slot_{d}_{t}_{date}_{time_str}", "<Button-1>", lambda e, d=d, t=t, date=date, time=time_str: self.open_event_popup(date, time))
        # Draw events
        for d in range(7):
            date = (self.current_week_start + timedelta(days=d)).strftime('%Y-%m-%d')
            if date in self.events:
                for idx, event in enumerate(self.events[date]):
                    start_h, start_m = map(int, event['start'].split(':'))
                    end_h, end_m = map(int, event['end'].split(':'))
                    start_y = 40 + (start_h - 8) * time_height + (start_m / 60) * time_height
                    end_y = 40 + (end_h - 8) * time_height + (end_m / 60) * time_height
                    x = d * day_width
                    rect = self.canvas.create_rectangle(x, start_y, x + day_width, end_y, fill='lightblue', outline='black', tags=f"event_{date}_{idx}")
                    event_text = f"{event['event']}\n{event['start']}-{event['end']}"
                    self.canvas.create_text(x + day_width / 2, (start_y + end_y) / 2, text=event_text, fill='black', font=('Arial', 9), tags=f"event_{date}_{idx}")
                    # Bind right-click to delete
                    self.canvas.tag_bind(f"event_{date}_{idx}", "<Button-3>", lambda e, d=date, i=idx: self.delete_event(d, i))

    def open_event_popup(self, date, time_str):
        """Open a popup window to add an event at a specific time"""
        popup = tk.Toplevel(self)
        popup.title(f"Add Event - {date} at {time_str}")
        popup.geometry("400x200")
        popup.config(bg='white')

        # Event name
        tk.Label(popup, text="Event Name:", bg='white', fg='black').pack(pady=5)
        event_entry = tk.Entry(popup, bg='white', fg='black', insertbackground='black')
        event_entry.pack(pady=5, padx=20, fill=tk.X)
        event_entry.focus()

        # Start time (pre-filled)
        tk.Label(popup, text="Start Time (HH:MM):", bg='white', fg='black').pack(pady=5)
        start_entry = tk.Entry(popup, bg='white', fg='black', insertbackground='black')
        start_entry.insert(0, time_str)
        start_entry.pack(pady=5, padx=20, fill=tk.X)

        # End time
        tk.Label(popup, text="End Time (HH:MM):", bg='white', fg='black').pack(pady=5)
        end_entry = tk.Entry(popup, bg='white', fg='black', insertbackground='black')
        # Default to 1 hour later
        start_h = int(time_str.split(':')[0])
        end_h = start_h + 1 if start_h < 20 else 20
        end_entry.insert(0, f"{end_h:02d}:00")
        end_entry.pack(pady=5, padx=20, fill=tk.X)

        def save_event():
            event = event_entry.get().strip()
            start = start_entry.get().strip()
            end = end_entry.get().strip()
            if event and start and end:
                try:
                    datetime.strptime(start, '%H:%M')
                    datetime.strptime(end, '%H:%M')
                    if date not in self.events:
                        self.events[date] = []
                    self.events[date].append({'event': event, 'start': start, 'end': end})
                    self.draw_week()
                    popup.destroy()
                except ValueError:
                    tk.messagebox.showerror("Error", "Invalid time format. Use HH:MM")
            else:
                tk.messagebox.showwarning("Warning", "Please fill all fields")

        # Bind Enter key to save
        event_entry.bind('<Return>', lambda e: save_event())

        tk.Button(popup, text="Save Event", command=save_event, bg='lightblue', fg='black', relief='raised', borderwidth=1).pack(pady=10)

    def delete_event(self, date, idx):
        """Delete an event by right-clicking on it"""
        if date in self.events and idx < len(self.events[date]):
            del self.events[date][idx]
            if not self.events[date]:
                del self.events[date]
            self.draw_week()

    def add_event(self):
        """Alternative method for adding events from the bottom input fields"""
        event = self.event_entry.get().strip()
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        date = self.calendar.get_date()
        if event and start and end and date:
            try:
                datetime.strptime(start, '%H:%M')
                datetime.strptime(end, '%H:%M')
                if date not in self.events:
                    self.events[date] = []
                self.events[date].append({'event': event, 'start': start, 'end': end})
                self.draw_week()
                self.event_entry.delete(0, tk.END)
                self.start_entry.delete(0, tk.END)
                self.end_entry.delete(0, tk.END)
            except ValueError:
                pass  # Invalid time format

    def load_data(self):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', [])
                events = data.get('events', {})
                self.events = {}
                for date, evs in events.items():
                    if isinstance(evs, list):
                        if evs and isinstance(evs[0], str):
                            # Old format, convert to new
                            self.events[date] = [{'event': e, 'start': '09:00', 'end': '10:00'} for e in evs]
                        else:
                            self.events[date] = evs
        except FileNotFoundError:
            pass

    def save_data(self):
        data = {'tasks': self.tasks, 'events': self.events}
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)

    def on_close(self):
        self.save_data()
        self.destroy()

if __name__ == "__main__":
    app = TodoCalendarApp()
    app.mainloop()