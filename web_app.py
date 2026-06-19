# pip install flask
import json
from datetime import datetime, timedelta
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# --- State (single-user, module-level) ---

state = {
    "tasks": [],       # [{'task': str, 'done': bool}, ...]
    "events": {},      # date_str -> [{'event': str, 'start': str, 'end': str}, ...]
    "current_week_start": None,  # set in load_data
}

DATA_FILE = "data.json"
TIMES = [f"{h:02d}:00" for h in range(8, 21)]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# --- Data persistence (identical logic to tkinter version) ---

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            state["tasks"] = data.get("tasks", [])
            events = data.get("events", {})
            state["events"] = {}
            for date, evs in events.items():
                if isinstance(evs, list):
                    if evs and isinstance(evs[0], str):
                        state["events"][date] = [
                            {"event": e, "start": "09:00", "end": "10:00"} for e in evs
                        ]
                    else:
                        state["events"][date] = evs
    except FileNotFoundError:
        pass
    now = datetime.now()
    state["current_week_start"] = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")


def save_data():
    # Strip any UI-only keys from tasks before saving
    clean_tasks = [{"task": t["task"], "done": t["done"]} for t in state["tasks"]]
    data = {"tasks": clean_tasks, "events": state["events"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Helpers ---

def week_start_dt():
    return datetime.strptime(state["current_week_start"], "%Y-%m-%d")


def week_dates():
    ws = week_start_dt()
    return [(ws + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]


def week_label():
    ws = week_start_dt()
    end = ws + timedelta(days=6)
    return f"Week of {ws.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"

# --- HTML template ---

PAGE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Professional To-Do &amp; Calendar Scheduler</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,system-ui,sans-serif;background:#1e1e2e;color:#cdd6f4;min-height:100vh}
a{color:#89b4fa;text-decoration:none}
.container{max-width:1100px;margin:0 auto;padding:10px}
h1{text-align:center;padding:14px 0 6px;font-size:1.3em;color:#cdd6f4}

/* Tabs */
.tabs{display:flex;gap:4px;margin-bottom:10px}
.tab-btn{flex:1;padding:10px;text-align:center;background:#313244;color:#cdd6f4;border:none;
  border-radius:8px 8px 0 0;font-size:1em;cursor:pointer}
.tab-btn.active{background:#45475a;color:#f5c2e7}
.tab-content{display:none;background:#181825;border-radius:0 0 8px 8px;padding:12px}
.tab-content.active{display:block}

/* To-Do */
.task-row{display:flex;align-items:center;background:#313244;border-radius:6px;padding:8px 12px;margin-bottom:6px}
.task-row .task-text{flex:1;margin:0 10px;font-size:1em}
.task-row .task-text.done{color:#a6e3a1;text-decoration:line-through}
.task-row .task-text.undone{color:#f38ba8}
.task-row form{display:inline}
.btn{background:#89b4fa;color:#1e1e2e;border:none;border-radius:4px;padding:6px 14px;
  cursor:pointer;font-size:.95em;font-weight:600}
.btn:active{opacity:.8}
.btn-danger{background:#f38ba8}
.btn-sm{padding:4px 10px;font-size:.85em}
.input-row{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.input-row input[type=text]{flex:1;min-width:120px;padding:8px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}

/* Calendar */
.nav-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.nav-row .week-label{font-weight:700;font-size:1em;text-align:center;flex:1}
.date-jump{display:flex;gap:6px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.date-jump input[type=date]{padding:6px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}

/* Week grid */
.week-grid{overflow-x:auto;-webkit-overflow-scrolling:touch}
table.cal{width:100%;border-collapse:collapse;min-width:640px}
table.cal th{background:#313244;color:#cdd6f4;padding:6px 4px;font-size:.85em;
  position:sticky;top:0;z-index:2}
table.cal td{border:1px solid #45475a;padding:2px 4px;vertical-align:top;height:44px;
  font-size:.8em;min-width:80px;position:relative}
table.cal td .time-label{color:#6c7086;font-size:.75em}
.event-block{background:#89b4fa;color:#1e1e2e;border-radius:4px;padding:2px 4px;margin:1px 0;
  font-size:.78em;display:flex;justify-content:space-between;align-items:center;gap:4px}
.event-block .ev-text{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.event-block form{flex-shrink:0}

/* Add-event row */
.event-input-row{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;align-items:end}
.event-input-row label{font-size:.85em;color:#a6adc8}
.event-input-row input[type=text],.event-input-row input[type=date]{
  padding:6px;border-radius:4px;border:1px solid #45475a;background:#313244;color:#cdd6f4;font-size:.95em}
.field{display:flex;flex-direction:column;gap:2px}
.field.grow{flex:1;min-width:120px}
.field.grow input{width:100%}

/* Slot add link */
td .slot-add{display:block;width:100%;height:100%;position:absolute;top:0;left:0;z-index:1}
td:hover{background:#313244}

/* Help */
.help-box{background:#313244;border-radius:8px;padding:14px 18px;margin-top:10px;
  font-size:.9em;line-height:1.6;white-space:pre-line}

/* Flash messages */
.flash{background:#f38ba8;color:#1e1e2e;padding:8px 14px;border-radius:6px;margin-bottom:8px;font-weight:600}
.flash.ok{background:#a6e3a1}
</style>
</head>
<body>
<div class="container">
<h1>Professional To-Do &amp; Calendar Scheduler</h1>

{% if flash_msg %}
<div class="flash {{ flash_cls }}">{{ flash_msg }}</div>
{% endif %}

<div class="tabs">
  <button class="tab-btn {% if tab == 'todo' %}active{% endif %}" onclick="showTab('todo')">To-Do List</button>
  <button class="tab-btn {% if tab == 'cal' %}active{% endif %}" onclick="showTab('cal')">Calendar &amp; Schedule</button>
  <button class="tab-btn" onclick="showTab('help')">Help</button>
</div>

<!-- ===== TO-DO TAB ===== -->
<div id="tab-todo" class="tab-content {% if tab == 'todo' %}active{% endif %}">
  {% for t in tasks %}
  <div class="task-row">
    <form method="post" action="/toggle_task/{{ loop.index0 }}">
      <input type="checkbox" onchange="this.form.submit()" {% if t.done %}checked{% endif %}>
    </form>
    <span class="task-text {{ 'done' if t.done else 'undone' }}">{{ t.task }}</span>
    <form method="post" action="/remove_task/{{ loop.index0 }}">
      <button type="submit" class="btn btn-danger btn-sm">&times;</button>
    </form>
  </div>
  {% endfor %}
  <form method="post" action="/add_task" class="input-row">
    <input type="text" name="task" placeholder="New task..." required>
    <button type="submit" class="btn">Add Task</button>
  </form>
</div>

<!-- ===== CALENDAR TAB ===== -->
<div id="tab-cal" class="tab-content {% if tab == 'cal' %}active{% endif %}">
  <!-- Date jump -->
  <form method="post" action="/select_date" class="date-jump">
    <input type="date" name="date" value="{{ selected_date }}">
    <button type="submit" class="btn btn-sm">Jump to date</button>
  </form>

  <!-- Week navigation -->
  <div class="nav-row">
    <form method="post" action="/prev_week"><button type="submit" class="btn btn-sm">&#9664;</button></form>
    <span class="week-label">{{ week_label }}</span>
    <form method="post" action="/next_week"><button type="submit" class="btn btn-sm">&#9654;</button></form>
  </div>

  <!-- Weekly grid -->
  <div class="week-grid">
  <table class="cal">
    <thead>
      <tr>
        <th>Time</th>
        {% for i in range(7) %}
        <th>{{ days[i] }}<br><small>{{ week_dates[i] }}</small></th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for time in times %}
      <tr>
        <td><span class="time-label">{{ time }}</span></td>
        {% for d in range(7) %}
        {% set date = week_dates[d] %}
        {% set cell_key = date ~ "|" ~ time %}
        <td>
          {% if cell_key in grid_events %}
            {% for ge in grid_events[cell_key] %}
            <div class="event-block">
              <span class="ev-text" title="{{ ge.event }} ({{ ge.start }}-{{ ge.end }})">{{ ge.event }} {{ ge.start }}-{{ ge.end }}</span>
              <form method="post" action="/delete_event/{{ date }}/{{ ge.idx }}">
                <button type="submit" class="btn btn-danger btn-sm">&times;</button>
              </form>
            </div>
            {% endfor %}
          {% endif %}
          {% set next_h = time.split(':')[0]|int + 1 %}
          {% set end_time = '%02d:00' % (next_h if next_h <= 20 else 20) %}
          <a class="slot-add" href="#event-form"
             onclick="prefill('{{ date }}','{{ time }}','{{ end_time }}')"
             title="Add event at {{ time }}"></a>
        </td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
  </div>

  <!-- Add-event form -->
  <form method="post" action="/add_event" class="event-input-row" id="event-form">
    <div class="field grow">
      <label>Event</label>
      <input type="text" name="event" id="ef-event" placeholder="Event name..." required>
    </div>
    <div class="field">
      <label>Date</label>
      <input type="date" name="date" id="ef-date" value="{{ selected_date }}" required>
    </div>
    <div class="field">
      <label>Start (HH:MM)</label>
      <input type="text" name="start" id="ef-start" placeholder="09:00" pattern="\d{2}:\d{2}" required>
    </div>
    <div class="field">
      <label>End (HH:MM)</label>
      <input type="text" name="end" id="ef-end" placeholder="10:00" pattern="\d{2}:\d{2}" required>
    </div>
    <button type="submit" class="btn">Add Event</button>
  </form>
</div>

<!-- ===== HELP TAB ===== -->
<div id="tab-help" class="tab-content">
<div class="help-box">TO-DO LIST CONTROLS:
- Check the checkbox to mark a task as done
- Click the X button to remove a task
- Red text = Unfinished, Green text = Finished
- Add new tasks in the input field at the bottom

CALENDAR &amp; SCHEDULE CONTROLS:
- Click on any time slot to pre-fill the add-event form
- Use the arrow buttons to navigate weeks
- Use "Jump to date" to go to a specific week
- Delete events with the X button on each event

TIPS:
- Data auto-saves after every action
- Times are in 24-hour format (HH:MM)
- The weekly view shows 08:00 to 20:00</div>
</div>

</div>

<script>
function showTab(name){
  document.querySelectorAll('.tab-content').forEach(function(el){el.classList.remove('active')});
  document.querySelectorAll('.tab-btn').forEach(function(el){el.classList.remove('active')});
  document.getElementById('tab-'+name).classList.add('active');
  // highlight button
  var btns=document.querySelectorAll('.tab-btn');
  var map={todo:0,cal:1,help:2};
  if(map[name]!==undefined) btns[map[name]].classList.add('active');
}
function prefill(date,start,end){
  document.getElementById('ef-date').value=date;
  document.getElementById('ef-start').value=start;
  document.getElementById('ef-end').value=end;
  document.getElementById('ef-event').focus();
}
</script>
</body>
</html>
"""

# --- Routes ---

@app.route("/")
def index():
    return render_page()


@app.route("/add_task", methods=["POST"])
def add_task():
    task_text = request.form.get("task", "").strip()
    if task_text:
        state["tasks"].append({"task": task_text, "done": False})
        save_data()
    return render_page(tab="todo")


@app.route("/toggle_task/<int:idx>", methods=["POST"])
def toggle_task(idx):
    if 0 <= idx < len(state["tasks"]):
        state["tasks"][idx]["done"] = not state["tasks"][idx]["done"]
        save_data()
    return render_page(tab="todo")


@app.route("/remove_task/<int:idx>", methods=["POST"])
def remove_task(idx):
    if 0 <= idx < len(state["tasks"]):
        state["tasks"].pop(idx)
        save_data()
    return render_page(tab="todo")


@app.route("/prev_week", methods=["POST"])
def prev_week():
    ws = week_start_dt() - timedelta(days=7)
    state["current_week_start"] = ws.strftime("%Y-%m-%d")
    return render_page(tab="cal")


@app.route("/next_week", methods=["POST"])
def next_week():
    ws = week_start_dt() + timedelta(days=7)
    state["current_week_start"] = ws.strftime("%Y-%m-%d")
    return render_page(tab="cal")


@app.route("/select_date", methods=["POST"])
def select_date():
    date_str = request.form.get("date", "")
    if date_str:
        try:
            selected = datetime.strptime(date_str, "%Y-%m-%d")
            state["current_week_start"] = (selected - timedelta(days=selected.weekday())).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return render_page(tab="cal")


@app.route("/add_event", methods=["POST"])
def add_event():
    event = request.form.get("event", "").strip()
    date = request.form.get("date", "").strip()
    start = request.form.get("start", "").strip()
    end = request.form.get("end", "").strip()
    flash_msg = ""
    flash_cls = ""
    if event and date and start and end:
        try:
            datetime.strptime(start, "%H:%M")
            datetime.strptime(end, "%H:%M")
            if date not in state["events"]:
                state["events"][date] = []
            state["events"][date].append({"event": event, "start": start, "end": end})
            save_data()
            # Jump to the week containing this event
            selected = datetime.strptime(date, "%Y-%m-%d")
            state["current_week_start"] = (selected - timedelta(days=selected.weekday())).strftime("%Y-%m-%d")
        except ValueError:
            flash_msg = "Invalid time format. Use HH:MM (e.g. 09:00)"
            flash_cls = ""
    else:
        flash_msg = "Please fill all fields"
        flash_cls = ""
    return render_page(tab="cal", flash_msg=flash_msg, flash_cls=flash_cls)


@app.route("/delete_event/<date>/<int:idx>", methods=["POST"])
def delete_event(date, idx):
    if date in state["events"] and idx < len(state["events"][date]):
        del state["events"][date][idx]
        if not state["events"][date]:
            del state["events"][date]
        save_data()
    return render_page(tab="cal")


def build_grid_events(wd):
    """Map each cell (date|HH:00) to the events whose start falls in that hour."""
    grid = {}
    for date in wd:
        if date not in state["events"]:
            continue
        for idx, ev in enumerate(state["events"][date]):
            try:
                sh = int(ev["start"].split(":")[0])
            except (ValueError, IndexError):
                continue
            slot = f"{sh:02d}:00"
            key = f"{date}|{slot}"
            grid.setdefault(key, []).append({**ev, "idx": idx})
    return grid


def render_page(tab="todo", flash_msg="", flash_cls=""):
    wd = week_dates()
    selected = state["current_week_start"]
    return render_template_string(
        PAGE_HTML,
        tab=tab,
        tasks=state["tasks"],
        events=state["events"],
        times=TIMES,
        days=DAYS,
        week_dates=wd,
        week_label=week_label(),
        selected_date=selected,
        flash_msg=flash_msg,
        flash_cls=flash_cls,
        grid_events=build_grid_events(wd),
    )

# --- Startup ---

if __name__ == "__main__":
    load_data()
    print("=" * 50)
    print("  To-Do & Calendar Scheduler")
    print("  Open in your browser:")
    print("  http://127.0.0.1:8765")
    print("=" * 50)
    app.run(host="127.0.0.1", port=8765, debug=False)
