# No dependencies required - uses only Python standard library
import json
import html
import re
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, unquote

# --- State (single-user, module-level) ---

state = {
    "tasks": [],
    "events": {},
    "current_week_start": None,
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
    clean_tasks = [{"task": t["task"], "done": t["done"]} for t in state["tasks"]]
    data = {"tasks": clean_tasks, "events": state["events"]}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Helpers ---

def week_start_dt():
    return datetime.strptime(state["current_week_start"], "%Y-%m-%d")


def week_dates_list():
    ws = week_start_dt()
    return [(ws + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]


def week_label():
    ws = week_start_dt()
    end = ws + timedelta(days=6)
    return f"Week of {ws.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"


def build_grid_events(wd):
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
            entry = dict(ev)
            entry["idx"] = idx
            grid.setdefault(key, []).append(entry)
    return grid


def h(text):
    return html.escape(str(text))

# --- HTML builder ---

def render_page(tab="todo", flash_msg=""):
    wd = week_dates_list()
    wl = week_label()
    selected = state["current_week_start"]
    grid = build_grid_events(wd)

    # Task rows
    task_rows = ""
    for i, t in enumerate(state["tasks"]):
        css = "done" if t["done"] else "undone"
        checked = " checked" if t["done"] else ""
        task_rows += f'''<div class="task-row">
<form method="post" action="/toggle_task/{i}">
  <input type="checkbox" onchange="this.form.submit()"{checked}>
</form>
<span class="task-text {css}">{h(t["task"])}</span>
<form method="post" action="/remove_task/{i}">
  <button type="submit" class="btn btn-danger btn-sm">&times;</button>
</form>
</div>\n'''

    # Calendar grid rows
    cal_rows = ""
    for time in TIMES:
        cal_rows += f'<tr><td><span class="time-label">{time}</span></td>\n'
        for d in range(7):
            date = wd[d]
            cell_key = f"{date}|{time}"
            events_html = ""
            if cell_key in grid:
                for ge in grid[cell_key]:
                    events_html += f'''<div class="event-block">
<span class="ev-text" title="{h(ge["event"])} ({h(ge["start"])}-{h(ge["end"])})">{h(ge["event"])} {h(ge["start"])}-{h(ge["end"])}</span>
<form method="post" action="/delete_event/{date}/{ge["idx"]}">
  <button type="submit" class="btn btn-danger btn-sm">&times;</button>
</form>
</div>\n'''
            hour = int(time.split(":")[0])
            next_h = hour + 1 if hour < 20 else 20
            end_time = f"{next_h:02d}:00"
            cal_rows += f'''<td>{events_html}<a class="slot-add" href="#event-form"
onclick="prefill('{date}','{time}','{end_time}')"
title="Add event at {time}"></a></td>\n'''
        cal_rows += "</tr>\n"

    # Day headers
    day_headers = '<th>Time</th>\n'
    for i in range(7):
        day_headers += f'<th>{DAYS[i]}<br><small>{wd[i]}</small></th>\n'

    # Tab active classes
    todo_active = " active" if tab == "todo" else ""
    cal_active = " active" if tab == "cal" else ""
    todo_btn = " active" if tab == "todo" else ""
    cal_btn = " active" if tab == "cal" else ""

    flash_html = ""
    if flash_msg:
        flash_html = f'<div class="flash">{h(flash_msg)}</div>\n'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Professional To-Do &amp; Calendar Scheduler</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,system-ui,sans-serif;background:#1e1e2e;color:#cdd6f4;min-height:100vh}}
a{{color:#89b4fa;text-decoration:none}}
.container{{max-width:1100px;margin:0 auto;padding:10px}}
h1{{text-align:center;padding:14px 0 6px;font-size:1.3em;color:#cdd6f4}}
.tabs{{display:flex;gap:4px;margin-bottom:10px}}
.tab-btn{{flex:1;padding:10px;text-align:center;background:#313244;color:#cdd6f4;border:none;
  border-radius:8px 8px 0 0;font-size:1em;cursor:pointer}}
.tab-btn.active{{background:#45475a;color:#f5c2e7}}
.tab-content{{display:none;background:#181825;border-radius:0 0 8px 8px;padding:12px}}
.tab-content.active{{display:block}}
.task-row{{display:flex;align-items:center;background:#313244;border-radius:6px;padding:8px 12px;margin-bottom:6px}}
.task-row .task-text{{flex:1;margin:0 10px;font-size:1em}}
.task-row .task-text.done{{color:#a6e3a1;text-decoration:line-through}}
.task-row .task-text.undone{{color:#f38ba8}}
.task-row form{{display:inline}}
.btn{{background:#89b4fa;color:#1e1e2e;border:none;border-radius:4px;padding:6px 14px;
  cursor:pointer;font-size:.95em;font-weight:600}}
.btn:active{{opacity:.8}}
.btn-danger{{background:#f38ba8}}
.btn-sm{{padding:4px 10px;font-size:.85em}}
.input-row{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}}
.input-row input[type=text]{{flex:1;min-width:120px;padding:8px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}}
.nav-row{{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}}
.nav-row .week-label{{font-weight:700;font-size:1em;text-align:center;flex:1}}
.date-jump{{display:flex;gap:6px;align-items:center;margin-bottom:10px;flex-wrap:wrap}}
.date-jump input[type=date]{{padding:6px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}}
.week-grid{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table.cal{{width:100%;border-collapse:collapse;min-width:640px}}
table.cal th{{background:#313244;color:#cdd6f4;padding:6px 4px;font-size:.85em;
  position:sticky;top:0;z-index:2}}
table.cal td{{border:1px solid #45475a;padding:2px 4px;vertical-align:top;height:44px;
  font-size:.8em;min-width:80px;position:relative}}
table.cal td .time-label{{color:#6c7086;font-size:.75em}}
.event-block{{background:#89b4fa;color:#1e1e2e;border-radius:4px;padding:2px 4px;margin:1px 0;
  font-size:.78em;display:flex;justify-content:space-between;align-items:center;gap:4px}}
.event-block .ev-text{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.event-block form{{flex-shrink:0}}
.event-input-row{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;align-items:end}}
.event-input-row label{{font-size:.85em;color:#a6adc8}}
.event-input-row input[type=text],.event-input-row input[type=date]{{
  padding:6px;border-radius:4px;border:1px solid #45475a;background:#313244;color:#cdd6f4;font-size:.95em}}
.field{{display:flex;flex-direction:column;gap:2px}}
.field.grow{{flex:1;min-width:120px}}
.field.grow input{{width:100%}}
td .slot-add{{display:block;width:100%;height:100%;position:absolute;top:0;left:0;z-index:1}}
td:hover{{background:#313244}}
.help-box{{background:#313244;border-radius:8px;padding:14px 18px;margin-top:10px;
  font-size:.9em;line-height:1.6;white-space:pre-line}}
.flash{{background:#f38ba8;color:#1e1e2e;padding:8px 14px;border-radius:6px;margin-bottom:8px;font-weight:600}}
</style>
</head>
<body>
<div class="container">
<h1>Professional To-Do &amp; Calendar Scheduler</h1>
{flash_html}
<div class="tabs">
  <button class="tab-btn{todo_btn}" onclick="showTab('todo')">To-Do List</button>
  <button class="tab-btn{cal_btn}" onclick="showTab('cal')">Calendar &amp; Schedule</button>
  <button class="tab-btn" onclick="showTab('help')">Help</button>
</div>

<div id="tab-todo" class="tab-content{todo_active}">
{task_rows}
  <form method="post" action="/add_task" class="input-row">
    <input type="text" name="task" placeholder="New task..." required>
    <button type="submit" class="btn">Add Task</button>
  </form>
</div>

<div id="tab-cal" class="tab-content{cal_active}">
  <form method="post" action="/select_date" class="date-jump">
    <input type="date" name="date" value="{selected}">
    <button type="submit" class="btn btn-sm">Jump to date</button>
  </form>
  <div class="nav-row">
    <form method="post" action="/prev_week"><button type="submit" class="btn btn-sm">&#9664;</button></form>
    <span class="week-label">{h(wl)}</span>
    <form method="post" action="/next_week"><button type="submit" class="btn btn-sm">&#9654;</button></form>
  </div>
  <div class="week-grid">
  <table class="cal">
    <thead><tr>{day_headers}</tr></thead>
    <tbody>{cal_rows}</tbody>
  </table>
  </div>
  <form method="post" action="/add_event" class="event-input-row" id="event-form">
    <div class="field grow">
      <label>Event</label>
      <input type="text" name="event" id="ef-event" placeholder="Event name..." required>
    </div>
    <div class="field">
      <label>Date</label>
      <input type="date" name="date" id="ef-date" value="{selected}" required>
    </div>
    <div class="field">
      <label>Start (HH:MM)</label>
      <input type="text" name="start" id="ef-start" placeholder="09:00" pattern="\\d{{2}}:\\d{{2}}" required>
    </div>
    <div class="field">
      <label>End (HH:MM)</label>
      <input type="text" name="end" id="ef-end" placeholder="10:00" pattern="\\d{{2}}:\\d{{2}}" required>
    </div>
    <button type="submit" class="btn">Add Event</button>
  </form>
</div>

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
function showTab(name){{
  document.querySelectorAll('.tab-content').forEach(function(el){{el.classList.remove('active')}});
  document.querySelectorAll('.tab-btn').forEach(function(el){{el.classList.remove('active')}});
  document.getElementById('tab-'+name).classList.add('active');
  var btns=document.querySelectorAll('.tab-btn');
  var map={{todo:0,cal:1,help:2}};
  if(map[name]!==undefined) btns[map[name]].classList.add('active');
}}
function prefill(date,start,end){{
  document.getElementById('ef-date').value=date;
  document.getElementById('ef-start').value=start;
  document.getElementById('ef-end').value=end;
  document.getElementById('ef-event').focus();
}}
</script>
</body>
</html>'''

# --- HTTP request handler ---

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_html(self, body, code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location="/"):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Connection", "close")
        self.end_headers()

    def _read_form(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw)
        return {k: v[0] for k, v in parsed.items()}

    def do_GET(self):
        self._send_html(render_page())

    def do_POST(self):
        path = self.path
        form = self._read_form()

        if path == "/add_task":
            task_text = form.get("task", "").strip()
            if task_text:
                state["tasks"].append({"task": task_text, "done": False})
                save_data()
            self._send_html(render_page(tab="todo"))

        elif path.startswith("/toggle_task/"):
            try:
                idx = int(path.split("/")[-1])
                if 0 <= idx < len(state["tasks"]):
                    state["tasks"][idx]["done"] = not state["tasks"][idx]["done"]
                    save_data()
            except ValueError:
                pass
            self._send_html(render_page(tab="todo"))

        elif path.startswith("/remove_task/"):
            try:
                idx = int(path.split("/")[-1])
                if 0 <= idx < len(state["tasks"]):
                    state["tasks"].pop(idx)
                    save_data()
            except ValueError:
                pass
            self._send_html(render_page(tab="todo"))

        elif path == "/prev_week":
            ws = week_start_dt() - timedelta(days=7)
            state["current_week_start"] = ws.strftime("%Y-%m-%d")
            self._send_html(render_page(tab="cal"))

        elif path == "/next_week":
            ws = week_start_dt() + timedelta(days=7)
            state["current_week_start"] = ws.strftime("%Y-%m-%d")
            self._send_html(render_page(tab="cal"))

        elif path == "/select_date":
            date_str = form.get("date", "")
            if date_str:
                try:
                    selected = datetime.strptime(date_str, "%Y-%m-%d")
                    state["current_week_start"] = (
                        selected - timedelta(days=selected.weekday())
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    pass
            self._send_html(render_page(tab="cal"))

        elif path == "/add_event":
            event = form.get("event", "").strip()
            date = form.get("date", "").strip()
            start = form.get("start", "").strip()
            end = form.get("end", "").strip()
            flash_msg = ""
            if event and date and start and end:
                try:
                    datetime.strptime(start, "%H:%M")
                    datetime.strptime(end, "%H:%M")
                    if date not in state["events"]:
                        state["events"][date] = []
                    state["events"][date].append(
                        {"event": event, "start": start, "end": end}
                    )
                    save_data()
                    selected = datetime.strptime(date, "%Y-%m-%d")
                    state["current_week_start"] = (
                        selected - timedelta(days=selected.weekday())
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    flash_msg = "Invalid time format. Use HH:MM (e.g. 09:00)"
            else:
                flash_msg = "Please fill all fields"
            self._send_html(render_page(tab="cal", flash_msg=flash_msg))

        elif path.startswith("/delete_event/"):
            parts = path.split("/")
            if len(parts) == 4:
                date = parts[2]
                try:
                    idx = int(parts[3])
                    if date in state["events"] and idx < len(state["events"][date]):
                        del state["events"][date][idx]
                        if not state["events"][date]:
                            del state["events"][date]
                        save_data()
                except ValueError:
                    pass
            self._send_html(render_page(tab="cal"))

        else:
            self._send_html(render_page())

# --- Startup ---

if __name__ == "__main__":
    load_data()
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("=" * 50)
    print("  To-Do & Calendar Scheduler")
    print("  Open in your browser:")
    print("  http://127.0.0.1:8765")
    print("=" * 50)
    server.serve_forever()
