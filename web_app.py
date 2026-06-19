# No dependencies required - uses only Python standard library
# Generates index.html then opens a local server to serve it
import json
import html
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

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

def e(text):
    return html.escape(str(text))

# --- HTML page builder ---

def render_page(tab="todo", flash_msg=""):
    wd = week_dates_list()
    wl = week_label()
    selected = state["current_week_start"]
    grid = build_grid_events(wd)

    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>To-Do &amp; Calendar Scheduler</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,system-ui,sans-serif;background:#1e1e2e;color:#cdd6f4;
  min-height:100vh;padding:10px}
h1{text-align:center;padding:10px 0;font-size:1.3em}
.tabs{display:flex;gap:4px;margin-bottom:10px}
.tabs button{flex:1;padding:10px;background:#313244;color:#cdd6f4;border:none;
  border-radius:8px 8px 0 0;font-size:1em;cursor:pointer}
.tabs button.on{background:#45475a;color:#f5c2e7}
.panel{display:none;background:#181825;border-radius:0 0 8px 8px;padding:12px}
.panel.on{display:block}
.task{display:flex;align-items:center;background:#313244;border-radius:6px;
  padding:8px 12px;margin-bottom:6px}
.task span{flex:1;margin:0 10px}
.task .undone{color:#f38ba8}
.task .done{color:#a6e3a1;text-decoration:line-through}
.task form{display:inline}
.b{background:#89b4fa;color:#1e1e2e;border:none;border-radius:4px;padding:6px 14px;
  cursor:pointer;font-size:.95em;font-weight:600}
.b:active{opacity:.7}
.bd{background:#f38ba8}
.bs{padding:4px 10px;font-size:.85em}
.row{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.row input[type=text],.row input[type=date]{flex:1;min-width:100px;padding:8px;
  border-radius:4px;border:1px solid #45475a;background:#313244;color:#cdd6f4;font-size:1em}
.nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.nav .wl{font-weight:700;text-align:center;flex:1}
.dj{display:flex;gap:6px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.dj input[type=date]{padding:6px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}
.wg{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;min-width:640px}
th{background:#313244;padding:6px 4px;font-size:.85em;position:sticky;top:0;z-index:2}
td{border:1px solid #45475a;padding:2px 4px;vertical-align:top;height:44px;
  font-size:.8em;min-width:80px}
td:hover{background:#313244}
.tl{color:#6c7086;font-size:.75em}
.ev{background:#89b4fa;color:#1e1e2e;border-radius:4px;padding:2px 4px;margin:1px 0;
  font-size:.78em;display:flex;justify-content:space-between;align-items:center;gap:4px}
.ev span{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ev form{flex-shrink:0}
.ef{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;align-items:end}
.ef label{font-size:.85em;color:#a6adc8}
.ef input{padding:6px;border-radius:4px;border:1px solid #45475a;background:#313244;
  color:#cdd6f4;font-size:.95em}
.fg{display:flex;flex-direction:column;gap:2px}
.fg.w{flex:1;min-width:100px}
.fg.w input{width:100%}
.hb{background:#313244;border-radius:8px;padding:14px 18px;font-size:.9em;
  line-height:1.6;white-space:pre-line}
.fl{background:#f38ba8;color:#1e1e2e;padding:8px 14px;border-radius:6px;
  margin-bottom:8px;font-weight:600}
</style>
</head>
<body>
<h1>To-Do &amp; Calendar Scheduler</h1>
""")

    if flash_msg:
        parts.append(f'<div class="fl">{e(flash_msg)}</div>\n')

    todo_on = " on" if tab == "todo" else ""
    cal_on = " on" if tab == "cal" else ""

    parts.append(f"""<div class="tabs">
<button class="{('on' if tab=='todo' else '')}" onclick="T('todo')">To-Do List</button>
<button class="{('on' if tab=='cal' else '')}" onclick="T('cal')">Calendar</button>
<button onclick="T('help')">Help</button>
</div>
""")

    # --- To-Do panel ---
    parts.append(f'<div id="todo" class="panel{todo_on}">\n')
    for i, t in enumerate(state["tasks"]):
        cls = "done" if t["done"] else "undone"
        chk = " checked" if t["done"] else ""
        parts.append(f'''<div class="task">
<form method="post" action="/toggle/{i}"><input type="checkbox" onchange="this.form.submit()"{chk}></form>
<span class="{cls}">{e(t["task"])}</span>
<form method="post" action="/del/{i}"><button class="b bd bs" type="submit">&times;</button></form>
</div>\n''')
    parts.append('''<form method="post" action="/add" class="row">
<input type="text" name="task" placeholder="New task..." required>
<button type="submit" class="b">Add Task</button>
</form>
</div>\n''')

    # --- Calendar panel ---
    parts.append(f'<div id="cal" class="panel{cal_on}">\n')
    parts.append(f'''<form method="post" action="/jump" class="dj">
<input type="date" name="date" value="{selected}">
<button type="submit" class="b bs">Jump to date</button>
</form>
<div class="nav">
<form method="post" action="/pw"><button type="submit" class="b bs">&#9664;</button></form>
<span class="wl">{e(wl)}</span>
<form method="post" action="/nw"><button type="submit" class="b bs">&#9654;</button></form>
</div>
<div class="wg"><table><thead><tr><th>Time</th>\n''')
    for i in range(7):
        parts.append(f"<th>{DAYS[i]}<br><small>{wd[i]}</small></th>\n")
    parts.append("</tr></thead><tbody>\n")

    for time in TIMES:
        parts.append(f'<tr><td><span class="tl">{time}</span></td>\n')
        for d in range(7):
            date = wd[d]
            cell_key = f"{date}|{time}"
            parts.append("<td>")
            if cell_key in grid:
                for ge in grid[cell_key]:
                    parts.append(f'''<div class="ev">
<span title="{e(ge['event'])} ({ge['start']}-{ge['end']})">{e(ge['event'])} {ge['start']}-{ge['end']}</span>
<form method="post" action="/de/{date}/{ge['idx']}"><button class="b bd bs" type="submit">&times;</button></form>
</div>''')
            hour = int(time.split(":")[0])
            nh = hour + 1 if hour < 20 else 20
            et = f"{nh:02d}:00"
            parts.append(f'''<a href="#ef" onclick="P('{date}','{time}','{et}')" style="display:block;position:absolute;top:0;left:0;width:100%;height:100%"></a>''')
            parts.append("</td>\n")
        parts.append("</tr>\n")

    parts.append("</tbody></table></div>\n")

    parts.append(f'''<form method="post" action="/ae" class="ef" id="ef">
<div class="fg w"><label>Event</label><input type="text" name="event" id="fe" placeholder="Event name..." required></div>
<div class="fg"><label>Date</label><input type="date" name="date" id="fd" value="{selected}" required></div>
<div class="fg"><label>Start</label><input type="text" name="start" id="fs" placeholder="09:00" required></div>
<div class="fg"><label>End</label><input type="text" name="end" id="fn" placeholder="10:00" required></div>
<button type="submit" class="b">Add Event</button>
</form>
</div>\n''')

    # --- Help panel ---
    parts.append('''<div id="help" class="panel">
<div class="hb">TO-DO LIST CONTROLS:
- Check the checkbox to mark a task as done
- Click the X button to remove a task
- Red text = Unfinished, Green text = Finished
- Add new tasks in the input field at the bottom

CALENDAR CONTROLS:
- Click on any time slot to pre-fill the add-event form
- Use the arrow buttons to navigate weeks
- Use Jump to date to go to a specific week
- Delete events with the X button on each event

TIPS:
- Data auto-saves after every action
- Times are in 24-hour format (HH:MM)
- The weekly view shows 08:00 to 20:00</div>
</div>
''')

    parts.append("""<script>
function T(n){
var ps=document.querySelectorAll('.panel');
for(var i=0;i<ps.length;i++) ps[i].className='panel';
document.getElementById(n).className='panel on';
var bs=document.querySelectorAll('.tabs button');
for(var i=0;i<bs.length;i++) bs[i].className='';
var m={todo:0,cal:1,help:2};
if(m[n]!==undefined) bs[m[n]].className='on';
}
function P(d,s,en){
document.getElementById('fd').value=d;
document.getElementById('fs').value=s;
document.getElementById('fn').value=en;
document.getElementById('fe').focus();
}
</script>
</body>
</html>""")

    return "".join(parts)

# --- HTTP Server ---

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def _html(self, body, code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _form(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n).decode("utf-8")
        p = parse_qs(raw)
        return {k: v[0] for k, v in p.items()}

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        self._html(render_page())

    def do_POST(self):
        path = self.path
        form = self._form()

        if path == "/add":
            txt = form.get("task", "").strip()
            if txt:
                state["tasks"].append({"task": txt, "done": False})
                save_data()
            self._html(render_page(tab="todo"))

        elif path.startswith("/toggle/"):
            try:
                i = int(path.split("/")[-1])
                if 0 <= i < len(state["tasks"]):
                    state["tasks"][i]["done"] = not state["tasks"][i]["done"]
                    save_data()
            except ValueError:
                pass
            self._html(render_page(tab="todo"))

        elif path.startswith("/del/"):
            try:
                i = int(path.split("/")[-1])
                if 0 <= i < len(state["tasks"]):
                    state["tasks"].pop(i)
                    save_data()
            except ValueError:
                pass
            self._html(render_page(tab="todo"))

        elif path == "/pw":
            ws = week_start_dt() - timedelta(days=7)
            state["current_week_start"] = ws.strftime("%Y-%m-%d")
            self._html(render_page(tab="cal"))

        elif path == "/nw":
            ws = week_start_dt() + timedelta(days=7)
            state["current_week_start"] = ws.strftime("%Y-%m-%d")
            self._html(render_page(tab="cal"))

        elif path == "/jump":
            ds = form.get("date", "")
            if ds:
                try:
                    sel = datetime.strptime(ds, "%Y-%m-%d")
                    state["current_week_start"] = (sel - timedelta(days=sel.weekday())).strftime("%Y-%m-%d")
                except ValueError:
                    pass
            self._html(render_page(tab="cal"))

        elif path == "/ae":
            ev = form.get("event", "").strip()
            dt = form.get("date", "").strip()
            st = form.get("start", "").strip()
            en = form.get("end", "").strip()
            msg = ""
            if ev and dt and st and en:
                try:
                    datetime.strptime(st, "%H:%M")
                    datetime.strptime(en, "%H:%M")
                    state["events"].setdefault(dt, []).append({"event": ev, "start": st, "end": en})
                    save_data()
                    sel = datetime.strptime(dt, "%Y-%m-%d")
                    state["current_week_start"] = (sel - timedelta(days=sel.weekday())).strftime("%Y-%m-%d")
                except ValueError:
                    msg = "Invalid time format. Use HH:MM"
            else:
                msg = "Please fill all fields"
            self._html(render_page(tab="cal", flash_msg=msg))

        elif path.startswith("/de/"):
            parts = path.split("/")
            if len(parts) == 4:
                dt, idx = parts[2], parts[3]
                try:
                    idx = int(idx)
                    if dt in state["events"] and idx < len(state["events"][dt]):
                        del state["events"][dt][idx]
                        if not state["events"][dt]:
                            del state["events"][dt]
                        save_data()
                except ValueError:
                    pass
            self._html(render_page(tab="cal"))

        else:
            self._html(render_page())


if __name__ == "__main__":
    load_data()
    addr = ("127.0.0.1", 8765)
    server = ThreadingHTTPServer(addr, Handler)
    print("=" * 44)
    print("  To-Do & Calendar Scheduler")
    print("  Open in Safari:")
    print("  http://127.0.0.1:8765")
    print("=" * 44)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        save_data()
        print("\nSaved. Goodbye.")
