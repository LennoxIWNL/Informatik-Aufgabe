# No dependencies - uses only Python standard library
#
# USAGE (try in this order):
#   python3 web_app.py
#   Then open Safari and go to:  http://localhost:8765
#   If that doesn't work, try:   http://127.0.0.1:8765
#
import json
import html
import os
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs

# --- State ---

state = {"tasks": [], "events": {}, "week": None}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
TIMES = [f"{h:02d}:00" for h in range(8, 21)]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            state["tasks"] = data.get("tasks", [])
            raw = data.get("events", {})
            state["events"] = {}
            for date, evs in raw.items():
                if isinstance(evs, list):
                    if evs and isinstance(evs[0], str):
                        state["events"][date] = [{"event": e, "start": "09:00", "end": "10:00"} for e in evs]
                    else:
                        state["events"][date] = evs
    except FileNotFoundError:
        pass
    now = datetime.now()
    state["week"] = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")


def save_data():
    d = {"tasks": [{"task": t["task"], "done": t["done"]} for t in state["tasks"]], "events": state["events"]}
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=4)


def ws_dt():
    return datetime.strptime(state["week"], "%Y-%m-%d")


def week_dates():
    ws = ws_dt()
    return [(ws + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]


def esc(s):
    return html.escape(str(s))


def grid_events(wd):
    g = {}
    for date in wd:
        for idx, ev in enumerate(state["events"].get(date, [])):
            try:
                sh = int(ev["start"].split(":")[0])
            except (ValueError, IndexError):
                continue
            key = f"{date}|{sh:02d}:00"
            g.setdefault(key, []).append({**ev, "idx": idx})
    return g


# --- Full page HTML (all JS inline, works without separate files) ---

def page(tab="todo", flash=""):
    wd = week_dates()
    ws = ws_dt()
    we = ws + timedelta(days=6)
    wl = f"Week of {ws.strftime('%Y-%m-%d')} to {we.strftime('%Y-%m-%d')}"
    sel = state["week"]
    gr = grid_events(wd)

    tasks_html = ""
    for i, t in enumerate(state["tasks"]):
        cls = "done" if t["done"] else "undone"
        chk = " checked" if t["done"] else ""
        tasks_html += f'''<div class="task">
<form method="post" action="/toggle/{i}"><button type="submit" class="cb{' cbd' if t['done'] else ''}">{('&#10003;' if t['done'] else '&nbsp;')}</button></form>
<span class="{cls}">{esc(t['task'])}</span>
<form method="post" action="/del/{i}"><button type="submit" class="b bd bs">&times;</button></form></div>
'''

    day_hdr = "<th>Time</th>"
    for i in range(7):
        day_hdr += f"<th>{DAYS[i]}<br><small>{wd[i]}</small></th>"

    cal_rows = ""
    for time in TIMES:
        cal_rows += f'<tr><td><span class="tl">{time}</span></td>'
        for d in range(7):
            date = wd[d]
            key = f"{date}|{time}"
            cell = ""
            if key in gr:
                for ge in gr[key]:
                    cell += f'<div class="ev"><span>{esc(ge["event"])} {ge["start"]}-{ge["end"]}</span>'
                    cell += f'<form method="post" action="/de/{date}/{ge["idx"]}"><button type="submit" class="b bd bs">&times;</button></form></div>'
            hour = int(time[:2])
            nh = hour + 1 if hour < 20 else 20
            cell += f'<a class="sa" href="/slot?d={date}&s={time}&e={nh:02d}:00">+</a>'
            cal_rows += f"<td>{cell}</td>"
        cal_rows += "</tr>"

    flash_html = f'<div class="fl">{esc(flash)}</div>' if flash else ""
    todo_on = " on" if tab == "todo" else ""
    cal_on = " on" if tab == "cal" else ""

    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>To-Do &amp; Calendar</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,system-ui,sans-serif;background:#1e1e2e;color:#cdd6f4;padding:0}}
h1{{text-align:center;padding:10px 0;font-size:1.3em;margin:0 10px}}
button,input{{font-family:inherit;font-size:inherit;-webkit-appearance:none}}
.top{{position:sticky;top:0;z-index:10;background:#1e1e2e;padding:0 10px 0}}
.tabs{{display:flex;gap:4px;padding-bottom:10px}}
.tabs a{{flex:1;padding:10px;background:#313244;color:#cdd6f4;border:none;
  border-radius:8px 8px 0 0;font-size:1em;text-align:center;text-decoration:none;display:block}}
.tabs a.on{{background:#45475a;color:#f5c2e7}}
.panel{{display:none;background:#181825;border-radius:0 0 8px 8px;padding:12px;margin:0 10px}}
.panel.on{{display:block}}
.task{{display:flex;align-items:center;background:#313244;border-radius:6px;padding:8px 12px;margin-bottom:6px}}
.task form{{display:inline}}
.task span{{flex:1;margin:0 10px;font-size:1em;word-break:break-word}}
.undone{{color:#f38ba8}}.done{{color:#a6e3a1;text-decoration:line-through}}
.cb{{width:28px;height:28px;background:#45475a;color:#cdd6f4;border:2px solid #6c7086;
  border-radius:4px;font-size:1em;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.cbd{{background:#89b4fa;border-color:#89b4fa;color:#1e1e2e}}
.b{{display:inline-block;background:#89b4fa;color:#1e1e2e;border:none;border-radius:4px;
  padding:8px 16px;font-size:.95em;font-weight:600;cursor:pointer;text-decoration:none}}
.b:active{{opacity:.7}}.bd{{background:#f38ba8}}.bs{{padding:6px 12px;font-size:.85em}}
.row{{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}}
input[type=text],input[type=date]{{padding:8px;border-radius:4px;border:1px solid #45475a;
  background:#313244;color:#cdd6f4;font-size:1em}}
.row input[type=text]{{flex:1;min-width:120px}}
.nav{{display:flex;align-items:center;margin-bottom:8px}}
.nav .wl{{font-weight:700;text-align:center;flex:1;font-size:.95em}}
.dj{{display:flex;gap:6px;align-items:center;margin-bottom:10px;flex-wrap:wrap}}
.wg{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{width:100%;border-collapse:collapse;min-width:640px}}
th{{background:#313244;padding:6px 4px;font-size:.85em;position:sticky;top:0;z-index:2}}
td{{border:1px solid #45475a;padding:2px 4px;vertical-align:top;height:44px;font-size:.8em;min-width:80px}}
td:hover{{background:#313244}}
.tl{{color:#6c7086;font-size:.75em}}
.ev{{background:#89b4fa;color:#1e1e2e;border-radius:4px;padding:3px 5px;margin:1px 0;
  font-size:.78em;display:flex;justify-content:space-between;align-items:center;gap:4px}}
.ev span{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.ev form{{flex-shrink:0}}
.sa{{display:inline-block;color:#45475a;text-decoration:none;font-size:.9em;padding:2px 6px;
  border-radius:4px;background:#313244;margin-top:2px}}
.sa:active{{background:#45475a}}
.ef{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;align-items:end}}
.ef label{{font-size:.85em;color:#a6adc8;display:block;margin-bottom:2px}}
.fg{{display:flex;flex-direction:column}}.fg.w{{flex:1;min-width:100px}}.fg.w input{{width:100%}}
.hb{{background:#313244;border-radius:8px;padding:14px 18px;font-size:.9em;line-height:1.6;white-space:pre-line}}
.fl{{background:#f38ba8;color:#1e1e2e;padding:8px 14px;border-radius:6px;margin-bottom:8px;font-weight:600}}
</style></head><body>
<div class="top" id="top">
<h1>To-Do &amp; Calendar</h1>
{flash_html}
<div class="tabs">
<a href="/?tab=todo#top" class="{('on' if tab=='todo' else '')}">To-Do List</a>
<a href="/?tab=cal#top" class="{('on' if tab=='cal' else '')}">Calendar</a>
<a href="/?tab=help#top">Help</a>
</div>
</div>
<div id="todo" class="panel{todo_on}">
{tasks_html}
<form method="post" action="/add" class="row">
<input type="text" name="task" placeholder="New task..." required>
<button type="submit" class="b">Add Task</button></form></div>
<div id="cal" class="panel{cal_on}">
<form method="post" action="/jump" class="dj">
<input type="date" name="date" value="{sel}">
<button type="submit" class="b bs">Jump to date</button></form>
<div class="nav">
<a href="/pw?tab=cal#top" class="b bs">&#9664;</a>
<span class="wl">{esc(wl)}</span>
<a href="/nw?tab=cal#top" class="b bs">&#9654;</a></div>
<div class="wg"><table><thead><tr>{day_hdr}</tr></thead><tbody>{cal_rows}</tbody></table></div>
<form method="post" action="/ae" class="ef" id="ef">
<div class="fg w"><label>Event</label><input type="text" name="event" id="ev-name" placeholder="Event name..." required></div>
<div class="fg"><label>Date</label><input type="date" name="date" id="ev-date" value="{sel}" required></div>
<div class="fg"><label>Start</label><input type="text" name="start" id="ev-start" placeholder="09:00" required></div>
<div class="fg"><label>End</label><input type="text" name="end" id="ev-end" placeholder="10:00" required></div>
<button type="submit" class="b">Add Event</button></form></div>
<div id="help" class="panel">
<div class="hb">TO-DO LIST:
- Tap checkbox to mark done/undone
- Tap X to remove a task
- Red = Unfinished, Green = Finished

CALENDAR:
- Tap + in a time slot to add an event there
- Use arrows to navigate weeks
- "Jump to date" goes to a specific week
- Tap X on an event to delete it

Data auto-saves after every action.
Times use 24h format (HH:MM), view: 08:00-20:00</div></div>
</body></html>'''


# --- Server ---

class Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def _html(self, body):
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _form(self):
        n = int(self.headers.get("Content-Length", 0))
        return {k: v[0] for k, v in parse_qs(self.rfile.read(n).decode()).items()}

    def _redir(self, url="/"):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def do_GET(self):
        p = self.path
        if p == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        tab = "todo"
        if "tab=cal" in p:
            tab = "cal"
        elif "tab=help" in p:
            tab = "help"

        if p.startswith("/pw"):
            state["week"] = (ws_dt() - timedelta(days=7)).strftime("%Y-%m-%d")
            tab = "cal"
        elif p.startswith("/nw"):
            state["week"] = (ws_dt() + timedelta(days=7)).strftime("%Y-%m-%d")
            tab = "cal"
        elif p.startswith("/slot?"):
            qs = dict(x.split("=") for x in p.split("?")[1].split("&"))
            return self._html(page(tab="cal").replace(
                'id="ev-date" value="' + state["week"],
                'id="ev-date" value="' + qs.get("d", state["week"])
            ).replace(
                'id="ev-start" placeholder="09:00"',
                'id="ev-start" placeholder="09:00" value="' + qs.get("s", "") + '"'
            ).replace(
                'id="ev-end" placeholder="10:00"',
                'id="ev-end" placeholder="10:00" value="' + qs.get("e", "") + '"'
            ))

        self._html(page(tab=tab))

    def do_POST(self):
        p = self.path
        form = self._form()

        if p == "/add":
            txt = form.get("task", "").strip()
            if txt:
                state["tasks"].append({"task": txt, "done": False})
                save_data()
            self._redir("/?tab=todo#top")

        elif p.startswith("/toggle/"):
            try:
                i = int(p.split("/")[-1])
                if 0 <= i < len(state["tasks"]):
                    state["tasks"][i]["done"] = not state["tasks"][i]["done"]
                    save_data()
            except ValueError:
                pass
            self._redir("/?tab=todo#top")

        elif p.startswith("/del/"):
            try:
                i = int(p.split("/")[-1])
                if 0 <= i < len(state["tasks"]):
                    state["tasks"].pop(i)
                    save_data()
            except ValueError:
                pass
            self._redir("/?tab=todo#top")

        elif p == "/jump":
            ds = form.get("date", "")
            if ds:
                try:
                    sel = datetime.strptime(ds, "%Y-%m-%d")
                    state["week"] = (sel - timedelta(days=sel.weekday())).strftime("%Y-%m-%d")
                except ValueError:
                    pass
            self._redir("/?tab=cal#top")

        elif p == "/ae":
            ev = form.get("event", "").strip()
            dt = form.get("date", "").strip()
            st = form.get("start", "").strip()
            en = form.get("end", "").strip()
            if ev and dt and st and en:
                try:
                    datetime.strptime(st, "%H:%M")
                    datetime.strptime(en, "%H:%M")
                    state["events"].setdefault(dt, []).append({"event": ev, "start": st, "end": en})
                    sel = datetime.strptime(dt, "%Y-%m-%d")
                    state["week"] = (sel - timedelta(days=sel.weekday())).strftime("%Y-%m-%d")
                    save_data()
                except ValueError:
                    pass
            self._redir("/?tab=cal#top")

        elif p.startswith("/de/"):
            parts = p.split("/")
            if len(parts) == 4:
                try:
                    dt, idx = parts[2], int(parts[3])
                    if dt in state["events"] and idx < len(state["events"][dt]):
                        del state["events"][dt][idx]
                        if not state["events"][dt]:
                            del state["events"][dt]
                        save_data()
                except ValueError:
                    pass
            self._redir("/?tab=cal#top")

        else:
            self._redir("/#top")

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    load_data()
    srv = Server(("127.0.0.1", 8765), H)
    url = "http://127.0.0.1:8765"
    print("=" * 44)
    print("  To-Do & Calendar Scheduler")
    print(f"  Oeffne Safari und gehe zu:")
    print(f"  {url}")
    print("=" * 44)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        save_data()
        print("\nGespeichert. Tschuess!")
