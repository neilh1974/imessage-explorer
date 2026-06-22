#!/usr/bin/env python3
# iMessage4Me
# search messages by keyword, contact, or date range
#
# requires: pip3 install flask
# Terminal needs Full Disk Access: System Settings > Privacy & Security

import sqlite3, shutil, os, tempfile, json
import glob, re
from datetime import datetime, timedelta

try:
    from flask import Flask, request, jsonify
    USE_FLASK = True
except ImportError:
    USE_FLASK = False
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs

APPLE_EPOCH = 978307200
PORT = 5001

# add your own email/phone here so your messages show as "Me"
MY_HANDLES = {
    "neilhe74@gmail.com",
    # "+12025551234",
}


def _normalize_phone(raw):
    digits = re.sub(r'\D', '', raw)
    return digits[-10:] if len(digits) >= 10 else digits

def build_contact_map():
    # pull contact names out of AddressBook so handles show as real names
    patterns = [
        os.path.expanduser("~/Library/Application Support/AddressBook/AddressBook-v22.abcddb"),
        os.path.expanduser("~/Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb"),
    ]
    db_path = None
    for pat in patterns:
        matches = glob.glob(pat)
        if matches:
            db_path = matches[0]
            break
    if not db_path or not os.path.exists(db_path):
        return {}

    fd, tmp = tempfile.mkstemp(suffix=".abcddb")
    os.close(fd)
    try:
        shutil.copy2(db_path, tmp)
        conn = sqlite3.connect(tmp)
        conn.row_factory = sqlite3.Row

        # rowid → display name
        names = {}
        for r in conn.execute("""
            SELECT Z_PK,
                   TRIM(COALESCE(ZFIRSTNAME,'') || ' ' || COALESCE(ZLASTNAME,'')) AS name,
                   COALESCE(ZORGANIZATION,'') AS org
            FROM ZABCDRECORD
        """):
            display = r["name"].strip() or r["org"].strip()
            if display:
                names[r["Z_PK"]] = display

        result = {}

        # Map emails
        for r in conn.execute("SELECT ZOWNER, ZADDRESS FROM ZABCDEMAILADDRESS WHERE ZADDRESS IS NOT NULL"):
            name = names.get(r["ZOWNER"])
            if name:
                result[r["ZADDRESS"].lower()] = name

        # Map phone numbers
        for r in conn.execute("SELECT ZOWNER, ZFULLNUMBER FROM ZABCDPHONENUMBER WHERE ZFULLNUMBER IS NOT NULL"):
            name = names.get(r["ZOWNER"])
            if name:
                result[_normalize_phone(r["ZFULLNUMBER"])] = name

        conn.close()
        return result
    except Exception:
        return {}
    finally:
        try: os.unlink(tmp)
        except: pass

_CONTACT_MAP = None

def get_contact_name(handle):
    global _CONTACT_MAP
    if _CONTACT_MAP is None:
        _CONTACT_MAP = build_contact_map()
    if not handle:
        return None
    low = handle.lower()
    if low in _CONTACT_MAP:
        return _CONTACT_MAP[low]
    # Try normalized phone
    norm = _normalize_phone(handle)
    return _CONTACT_MAP.get(norm)

REACTION_PREFIXES = (
    "Loved ", "Liked ", "Disliked ", "Laughed at ", "Emphasized ", "Questioned ",
)


def get_db_copy():
    src = os.path.expanduser("~/Library/Messages/chat.db")
    if not os.path.exists(src):
        raise FileNotFoundError("chat.db not found. Grant Full Disk Access to Terminal in System Settings.")
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    shutil.copy2(src, tmp)
    return tmp

def to_dt(apple_ts):
    if not apple_ts:
        return None
    # nanoseconds since 2001-01-01 on newer OS, seconds on older
    secs = apple_ts / 1e9 if apple_ts > 1e13 else float(apple_ts)
    try:
        return datetime.fromtimestamp(secs + APPLE_EPOCH)
    except Exception:
        return None

def fmt(dt, short=False):
    if not dt:
        return "Unknown"
    if short:
        if dt.date() == datetime.now().date():
            return dt.strftime("%I:%M %p").lstrip("0")
        if dt.year != datetime.now().year:
            return dt.strftime("%b %d, %Y")
        return dt.strftime("%b %d")
    return dt.strftime("%b %d, %Y · %I:%M %p")

def run_query(sql, params=()):
    db = get_db_copy()
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(sql, params)]
        conn.close()
        return rows
    finally:
        try: os.unlink(db)
        except: pass

def search_messages(query=None, contact=None, start_date=None, end_date=None, limit=5000):
    sql = """
        SELECT
            m.rowid                                     AS id,
            m.text                                      AS text,
            m.date                                      AS apple_date,
            m.is_from_me                                AS is_from_me,
            h.id                                        AS handle,
            COALESCE(c.display_name, h.id, 'Unknown')  AS chat_name,
            cmj.chat_id                                 AS chat_id
        FROM message m
        LEFT JOIN handle h              ON m.handle_id  = h.rowid
        LEFT JOIN chat_message_join cmj ON m.rowid      = cmj.message_id
        LEFT JOIN chat c                ON cmj.chat_id  = c.rowid
        WHERE m.text IS NOT NULL AND length(trim(m.text)) > 0
    """
    params = []
    for prefix in REACTION_PREFIXES:
        sql += " AND m.text NOT LIKE ?"
        params.append(f'{prefix}"%')

    if query:
        sql += " AND m.text LIKE ?"
        params.append(f"%{query}%")
    if contact:
        sql += " AND (h.id LIKE ? OR c.display_name LIKE ?)"
        params += [f"%{contact}%", f"%{contact}%"]
    if start_date:
        params.append(int((start_date - datetime(2001,1,1)).total_seconds() * 1e9))
        sql += " AND m.date >= ?"
    if end_date:
        eod = end_date.replace(hour=23, minute=59, second=59)
        params.append(int((eod - datetime(2001,1,1)).total_seconds() * 1e9))
        sql += " AND m.date <= ?"

    sql += " ORDER BY m.date DESC LIMIT ?"
    params.append(limit)

    results = []
    for r in run_query(sql, params):
        dt = to_dt(r["apple_date"])
        handle = r["handle"] or ""
        is_from_me = bool(r["is_from_me"]) or handle.lower() in {h.lower() for h in MY_HANDLES}
        resolved = get_contact_name(handle) or r["chat_name"] or handle or "Unknown"
        results.append({
            "id":         r["id"],
            "text":       r["text"],
            "date":       fmt(dt),
            "date_short": fmt(dt, short=True),
            "date_iso":   dt.isoformat() if dt else "",
            "is_from_me": is_from_me,
            "contact":    handle,
            "chat_name":  resolved,
            "chat_id":    r["chat_id"],
        })
    return results


def get_conversation(msg_id):
    """All messages in the same chat thread, oldest first."""
    rows = run_query("SELECT chat_id FROM chat_message_join WHERE message_id = ?", (msg_id,))
    if not rows:
        return "Unknown", []
    chat_id = rows[0]["chat_id"]

    chat_rows = run_query("SELECT COALESCE(display_name,'') as name FROM chat WHERE rowid = ?", (chat_id,))
    chat_name = chat_rows[0]["name"] if chat_rows else ""

    # filter out tapbacks same way search does
    reaction_conditions = " ".join(["AND m.text NOT LIKE ?" for _ in REACTION_PREFIXES])
    reaction_params = [f'{p}"%' for p in REACTION_PREFIXES]

    msgs = run_query(f"""
        SELECT m.rowid AS id, m.text, m.date AS apple_date, m.is_from_me, h.id AS handle
        FROM message m
        LEFT JOIN handle h              ON m.handle_id  = h.rowid
        LEFT JOIN chat_message_join cmj ON m.rowid      = cmj.message_id
        WHERE cmj.chat_id = ?
          AND m.text IS NOT NULL AND length(trim(m.text)) > 0
          {reaction_conditions}
        ORDER BY m.date ASC
    """, (chat_id, *reaction_params))

    results = []
    first_contact = None
    for r in msgs:
        handle = r["handle"] or ""
        is_from_me = bool(r["is_from_me"]) or handle.lower() in {h.lower() for h in MY_HANDLES}
        resolved = get_contact_name(handle) or handle
        if not is_from_me and handle and not first_contact:
            first_contact = resolved
        dt = to_dt(r["apple_date"])
        results.append({
            "id":         r["id"],
            "text":       r["text"],
            "date":       fmt(dt),
            "date_iso":   dt.isoformat() if dt else "",
            "is_from_me": is_from_me,
            "contact":    resolved or "Unknown",
        })

    name = chat_name or first_contact or "Unknown"
    return name, results


def get_memories(years_back=8):
    today = datetime.now()
    out = []
    for i in range(1, years_back + 1):
        target_year = today.year - i
        try:
            mid = today.replace(year=target_year, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            continue

        # widen the window until we find something
        msgs = []
        for days in [7, 30, 90, 183]:
            msgs = search_messages(
                start_date=mid - timedelta(days=days),
                end_date=mid   + timedelta(days=days),
                limit=20
            )
            if msgs:
                break

        if msgs:
            out.append({"year": target_year, "years_ago": i, "messages": msgs})
    return out


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>iMessage4Me</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif;
     background:#f5f5f7;color:#1d1d1f;height:100vh;display:flex;flex-direction:column;overflow:hidden}

.hdr{background:rgba(255,255,255,.9);backdrop-filter:blur(20px);
     border-bottom:1px solid rgba(0,0,0,.08);padding:12px 20px;
     display:flex;align-items:center;gap:16px;flex-shrink:0}
.hdr h1{font-size:17px;font-weight:700}
.hdr p{font-size:12px;color:#6e6e73}

.tabs{display:flex;gap:6px;padding:12px 20px 0;flex-shrink:0}
.tab{padding:7px 16px;border-radius:20px;border:1px solid #d2d2d7;
     background:white;color:#6e6e73;cursor:pointer;font-size:13px;font-weight:500}
.tab.active{background:#007aff;color:white;border-color:#007aff}

.workspace{display:flex;flex:1;overflow:hidden;gap:0}

.left-pane{display:flex;flex-direction:column;width:100%;flex-shrink:0;overflow:hidden;
           transition:width .25s ease}
.left-pane.split{width:38%}

.right-pane{flex:1;display:flex;flex-direction:column;background:white;
            border-left:1px solid #e5e5ea;overflow:hidden;
            transform:translateX(100%);transition:transform .25s ease;width:0}
.right-pane.open{transform:translateX(0);width:auto}

.bar{padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;
     border-bottom:1px solid #e5e5ea;background:white;flex-shrink:0}
.grp{display:flex;flex-direction:column;gap:3px}
.grp label{font-size:11px;font-weight:600;color:#6e6e73;text-transform:uppercase;letter-spacing:.4px}
input[type=text],input[type=date]{padding:8px 12px;border-radius:8px;
  border:1px solid #d2d2d7;font-size:13px;background:#f5f5f7;outline:none}
input:focus{border-color:#007aff;background:white;box-shadow:0 0 0 3px rgba(0,122,255,.12)}
#q-input{width:200px}
#c-input{width:160px}
.btn{padding:8px 16px;border-radius:8px;border:none;background:#007aff;
     color:white;font-size:13px;font-weight:500;cursor:pointer}
.btn:hover{background:#0066d6}
.btn-ghost{background:#f5f5f7;color:#1d1d1f;border:1px solid #d2d2d7}
.btn-ghost:hover{background:#e5e5ea}

.results{flex:1;overflow-y:auto;padding:8px}
.count{font-size:12px;color:#6e6e73;padding:6px 8px}

.card{padding:12px;border-radius:12px;margin-bottom:6px;cursor:pointer;
      border:1px solid rgba(0,0,0,.05);background:white;
      transition:background .1s,box-shadow .1s}
.card:hover{background:#f0f7ff;box-shadow:0 2px 8px rgba(0,122,255,.1)}
.card.active{background:#e8f0fe;border-color:#007aff}
.card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.card-who{font-size:12px;font-weight:600;color:#007aff}
.card-who.me{color:#34c759}
.card-when{font-size:11px;color:#6e6e73}
.card-text{font-size:14px;color:#1d1d1f;line-height:1.45;
           display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-text em{background:#fff176;font-style:normal;border-radius:2px;padding:0 1px}

.conv-hdr{padding:12px 16px;border-bottom:1px solid #e5e5ea;display:flex;
          align-items:center;gap:10px;background:white;flex-shrink:0}
.conv-back{background:none;border:none;color:#007aff;font-size:14px;cursor:pointer;
           font-weight:500;padding:4px 8px;border-radius:6px}
.conv-back:hover{background:#f0f7ff}
.conv-name{font-size:15px;font-weight:600;flex:1;text-align:center}
.conv-count{font-size:12px;color:#6e6e73}

.bubbles{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:4px;
         background:#f5f5f7}

.date-sep{text-align:center;font-size:11px;color:#6e6e73;
          margin:10px 0 6px;font-weight:500}

.brow{display:flex;align-items:flex-end;gap:6px;margin:1px 0}
.brow.me{flex-direction:row-reverse}

.bubble{max-width:72%;padding:9px 13px;border-radius:18px;
        font-size:14px;line-height:1.45;word-break:break-word;
        position:relative}
.brow.them .bubble{background:white;color:#1d1d1f;
                   border-bottom-left-radius:4px;
                   box-shadow:0 1px 2px rgba(0,0,0,.08)}
.brow.me   .bubble{background:#007aff;color:white;
                   border-bottom-right-radius:4px}
.bubble.target{outline:3px solid #ff9f0a;outline-offset:2px}

.btime{font-size:10px;color:#8e8e93;white-space:nowrap;padding-bottom:2px}

.empty{text-align:center;padding:48px 20px;color:#6e6e73}
.empty h3{font-size:16px;color:#1d1d1f;margin-bottom:6px}
.loading{text-align:center;padding:40px;color:#6e6e73;font-size:14px}

.mem-year{margin-bottom:28px}
.mem-y-hdr{font-size:20px;font-weight:700;padding:0 8px 2px}
.mem-y-sub{font-size:12px;color:#6e6e73;padding:0 8px 10px}

#search-panel,#memories-panel{display:none;flex-direction:column;flex:1;overflow:hidden}
#search-panel.active,#memories-panel.active{display:flex}
.tab-content{flex:1;display:flex;flex-direction:column;overflow:hidden}

.notice{background:#fff8e1;border-bottom:1px solid #ffe082;
        padding:10px 16px;font-size:12px;color:#795548;flex-shrink:0}
</style>
</head>
<body>

<div class="hdr">
  <div>
    <h1>💬 iMessage4Me</h1>
    <p id="hdr-sub">Loading your messages…</p>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="showTab('search',this)">🔍 Search</button>
  <button class="tab"        onclick="showTab('memories',this)">📅 Memories</button>
</div>

<div class="tab-content">

<!-- search -->
<div id="search-panel" class="active">
  <div class="notice">
    First run? If you see an error: System Settings → Privacy &amp; Security → Full Disk Access → add Terminal.
  </div>

  <div class="workspace">

    <div class="left-pane" id="left-pane">
      <div class="bar">
        <div class="grp">
          <label>Keyword</label>
          <input id="q-input" type="text" placeholder="Search…" onkeyup="if(event.key==='Enter')doSearch()">
        </div>
        <div class="grp">
          <label>Contact</label>
          <input id="c-input" type="text" placeholder="Name or number…" onkeyup="if(event.key==='Enter')doSearch()">
        </div>
        <div class="grp">
          <label>From</label>
          <input id="start" type="date">
        </div>
        <div class="grp">
          <label>To</label>
          <input id="end" type="date">
        </div>
        <button class="btn" onclick="doSearch()">Search</button>
        <button class="btn btn-ghost" onclick="clearSearch()">Clear</button>
      </div>
      <div class="results" id="search-results">
        <div class="loading">Loading recent messages…</div>
      </div>
    </div>

    <div class="right-pane" id="right-pane">
      <div class="conv-hdr">
        <button class="conv-back" onclick="closeConv()">← Back</button>
        <span class="conv-name" id="conv-name">Conversation</span>
        <span class="conv-count" id="conv-count"></span>
      </div>
      <div class="bubbles" id="bubbles"></div>
    </div>

  </div>
</div>

<!-- memories -->
<div id="memories-panel">
  <div class="workspace">
    <div class="left-pane" id="mem-left">
      <div class="results" id="memories-results">
        <div class="loading">Loading memories…</div>
      </div>
    </div>
    <div class="right-pane" id="mem-right-pane">
      <div class="conv-hdr">
        <button class="conv-back" onclick="closeMemConv()">← Back</button>
        <span class="conv-name" id="mem-conv-name">Conversation</span>
        <span class="conv-count" id="mem-conv-count"></span>
      </div>
      <div class="bubbles" id="mem-bubbles"></div>
    </div>
  </div>
</div>

</div><!-- /tab-content -->

<script>
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }

function highlight(text, q){
  if(!q) return esc(text)
  const re = new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi')
  return esc(text).replace(re,'<em>$1</em>')
}

function showTab(name, btn){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'))
  document.querySelectorAll('#search-panel,#memories-panel').forEach(p=>p.classList.remove('active'))
  btn.classList.add('active')
  document.getElementById(name+'-panel').classList.add('active')
  if(name==='memories') loadMemories()
}

let activeCard = null

function renderCards(msgs, q, clickFn){
  if(!msgs.length)
    return '<div class="empty"><h3>No messages found</h3><p>Try different terms or a wider date range</p></div>'
  return msgs.map(m=>`
    <div class="card" id="card-${m.id}" onclick="${clickFn}(${m.id}, this)">
      <div class="card-top">
        <span class="card-who ${m.is_from_me?'me':''}">${m.is_from_me ? '→ Me' : '← '+esc(m.chat_name||m.contact)}</span>
        <span class="card-when">${esc(m.date_short||m.date)}</span>
      </div>
      <div class="card-text">${highlight(m.text, q)}</div>
    </div>
  `).join('')
}

async function doSearch(){
  const q       = document.getElementById('q-input').value.trim()
  const contact = document.getElementById('c-input').value.trim()
  const start   = document.getElementById('start').value
  const end     = document.getElementById('end').value
  const el      = document.getElementById('search-results')
  el.innerHTML  = '<div class="loading">Searching…</div>'

  const p = new URLSearchParams()
  if(q)       p.set('q',q)
  if(contact) p.set('contact',contact)
  if(start)   p.set('start',start)
  if(end)     p.set('end',end)

  try{
    const res  = await fetch('/api/search?'+p)
    const data = await res.json()
    if(data.error) throw new Error(data.error)
    const label = (!q&&!contact&&!start&&!end)
      ? `${data.count} most recent messages — click any to open conversation`
      : `${data.count} result${data.count!==1?'s':''} — click to open conversation`
    document.getElementById('hdr-sub').textContent =
      (!q&&!contact&&!start&&!end) ? `${data.count} messages loaded` : `${data.count} results`
    el.innerHTML = `<div class="count">${label}</div>` + renderCards(data.messages, q, 'openConv')
  } catch(e){
    el.innerHTML = `<div class="empty"><h3>Error</h3><p>${esc(e.message)}</p></div>`
  }
}

function clearSearch(){
  ['q-input','c-input','start','end'].forEach(id=>document.getElementById(id).value='')
  closeConv()
  doSearch()
}

function fmtBubbleDate(iso){
  if(!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'})
       + ' · ' + d.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})
}

function renderBubbles(msgs, targetId){
  let html = ''
  let lastDate = null
  for(const m of msgs){
    const dayStr = m.date_iso ? m.date_iso.slice(0,10) : ''
    if(dayStr && dayStr !== lastDate){
      lastDate = dayStr
      const d = new Date(m.date_iso)
      html += `<div class="date-sep">${d.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'})}</div>`
    }
    const side  = m.is_from_me ? 'me' : 'them'
    const tgt   = m.id === targetId ? ' target' : ''
    html += `
      <div class="brow ${side}">
        <div class="bubble${tgt}" id="bubble-${m.id}">${esc(m.text)}</div>
        <span class="btime">${m.date_iso ? new Date(m.date_iso).toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'}) : ''}</span>
      </div>`
  }
  return html || '<div class="empty"><p>No messages</p></div>'
}

async function openConv(msgId, cardEl){
  if(activeCard) activeCard.classList.remove('active')
  activeCard = cardEl
  cardEl.classList.add('active')

  document.getElementById('bubbles').innerHTML = '<div class="loading">Loading conversation…</div>'
  document.getElementById('left-pane').classList.add('split')
  document.getElementById('right-pane').classList.add('open')

  try{
    const res  = await fetch('/api/conversation?msg_id='+msgId)
    const data = await res.json()
    if(data.error) throw new Error(data.error)

    document.getElementById('conv-name').textContent  = data.chat_name
    document.getElementById('conv-count').textContent = data.messages.length+' messages'
    document.getElementById('bubbles').innerHTML = renderBubbles(data.messages, msgId)

    const target = document.getElementById('bubble-'+msgId)
    if(target) target.scrollIntoView({behavior:'smooth', block:'center'})
  } catch(e){
    document.getElementById('bubbles').innerHTML = `<div class="empty"><p>${esc(e.message)}</p></div>`
  }
}

function closeConv(){
  document.getElementById('left-pane').classList.remove('split')
  document.getElementById('right-pane').classList.remove('open')
  if(activeCard){ activeCard.classList.remove('active'); activeCard=null }
}

let memLoaded = false

async function loadMemories(){
  if(memLoaded) return
  const el = document.getElementById('memories-results')
  try{
    const res  = await fetch('/api/memories')
    const data = await res.json()
    if(data.error) throw new Error(data.error)
    memLoaded = true
    if(!data.memories.length){
      el.innerHTML = '<div class="empty"><h3>No memories found</h3><p>No messages were found from this time in past years. If you have older messages, make sure Terminal has Full Disk Access in System Settings → Privacy &amp; Security.</p></div>'
      return
    }
    el.innerHTML = data.memories.map(m=>`
      <div class="mem-year">
        <div class="mem-y-hdr">📍 ${m.year}</div>
        <div class="mem-y-sub">${m.years_ago} year${m.years_ago!==1?'s':''} ago</div>
        ${renderCards(m.messages, null, 'openMemConv')}
      </div>
    `).join('')
  } catch(e){
    el.innerHTML = `<div class="empty"><h3>Error</h3><p>${esc(e.message)}</p></div>`
  }
}

let activeMemCard = null
async function openMemConv(msgId, cardEl){
  if(activeMemCard) activeMemCard.classList.remove('active')
  activeMemCard = cardEl
  cardEl.classList.add('active')

  document.getElementById('mem-bubbles').innerHTML = '<div class="loading">Loading…</div>'
  document.getElementById('mem-left').classList.add('split')
  document.getElementById('mem-right-pane').classList.add('open')

  try{
    const res  = await fetch('/api/conversation?msg_id='+msgId)
    const data = await res.json()
    if(data.error) throw new Error(data.error)
    document.getElementById('mem-conv-name').textContent  = data.chat_name
    document.getElementById('mem-conv-count').textContent = data.messages.length+' messages'
    document.getElementById('mem-bubbles').innerHTML = renderBubbles(data.messages, msgId)
    const target = document.getElementById('mem-bubbles').querySelector('[id="bubble-'+msgId+'"]')
    if(target) target.scrollIntoView({behavior:'smooth', block:'center'})
  } catch(e){
    document.getElementById('mem-bubbles').innerHTML = `<div class="empty"><p>${esc(e.message)}</p></div>`
  }
}

function closeMemConv(){
  document.getElementById('mem-left').classList.remove('split')
  document.getElementById('mem-right-pane').classList.remove('open')
  if(activeMemCard){ activeMemCard.classList.remove('active'); activeMemCard=null }
}

doSearch()
</script>
</body>
</html>"""

if USE_FLASK:
    app = Flask(__name__)
    app.json.sort_keys = False

    @app.route("/")
    def index(): return HTML

    @app.route("/api/search")
    def api_search():
        try:
            q       = request.args.get("q") or None
            contact = request.args.get("contact") or None
            start   = datetime.strptime(request.args["start"], "%Y-%m-%d") if request.args.get("start") else None
            end     = datetime.strptime(request.args["end"],   "%Y-%m-%d") if request.args.get("end")   else None
            msgs    = search_messages(query=q, contact=contact, start_date=start, end_date=end)
            return jsonify({"messages": msgs, "count": len(msgs)})
        except Exception as e:
            return jsonify({"error": str(e), "messages": [], "count": 0}), 500

    @app.route("/api/conversation")
    def api_conversation():
        try:
            msg_id = int(request.args.get("msg_id", 0))
            name, msgs = get_conversation(msg_id)
            return jsonify({"chat_name": name, "messages": msgs, "target_id": msg_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/memories")
    def api_memories():
        try:
            return jsonify({"memories": get_memories()})
        except Exception as e:
            return jsonify({"error": str(e), "memories": []}), 500

    @app.route("/debug")
    def debug():
        try:
            rows = run_query("""
                SELECT strftime('%Y', datetime(date/1000000000+978307200,'unixepoch','localtime')) AS year,
                       COUNT(*) AS count
                FROM message WHERE date>0 AND text IS NOT NULL AND length(trim(text))>0
                GROUP BY year ORDER BY year DESC LIMIT 15
            """)
            html = "<h2 style='font-family:monospace;padding:20px'>DB date distribution</h2><table border=1 cellpadding=6 style='border-collapse:collapse;font-family:monospace;margin:0 20px'><tr><th>Year</th><th>Messages</th></tr>"
            for r in rows:
                html += f"<tr><td>{r['year']}</td><td>{r['count']}</td></tr>"
            html += "</table>"

            # Show what memories query actually finds for each year
            from datetime import datetime, timedelta
            today = datetime.now()
            html += "<h2 style='font-family:monospace;padding:20px 20px 8px'>Memories query results</h2>"
            html += "<table border=1 cellpadding=6 style='border-collapse:collapse;font-family:monospace;margin:0 20px'><tr><th>Year</th><th>Window</th><th>Raw count (no filters)</th><th>Filtered count</th></tr>"
            for i in range(1, 6):
                try:
                    mid = today.replace(year=today.year - i, hour=0, minute=0, second=0, microsecond=0)
                except ValueError:
                    continue
                s = mid - timedelta(days=7)
                e = (mid + timedelta(days=7)).replace(hour=23, minute=59, second=59)
                s_ts = int((s - datetime(2001,1,1)).total_seconds() * 1e9)
                e_ts = int((e - datetime(2001,1,1)).total_seconds() * 1e9)

                raw = run_query("SELECT COUNT(*) as c FROM message WHERE date >= ? AND date <= ?", (s_ts, e_ts))
                filtered = run_query("SELECT COUNT(*) as c FROM message WHERE date >= ? AND date <= ? AND text IS NOT NULL AND length(trim(text))>0", (s_ts, e_ts))
                raw_c = raw[0]['c'] if raw else 0
                filt_c = filtered[0]['c'] if filtered else 0
                html += f"<tr><td>{today.year-i}</td><td>{s.strftime('%b %d')} – {e.strftime('%b %d')}</td><td>{raw_c}</td><td>{filt_c}</td></tr>"
            return html + "</table>"
        except Exception as e:
            import traceback
            return f"<pre>Error: {e}\n{traceback.format_exc()}</pre>", 500

else:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send_json(self, data, code=200):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",len(body))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            qs     = parse_qs(parsed.query)

            if parsed.path == "/":
                body = HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Content-Length",len(body))
                self.end_headers()
                self.wfile.write(body)

            elif parsed.path == "/api/search":
                try:
                    q       = qs["q"][0]       if "q"       in qs else None
                    contact = qs["contact"][0] if "contact" in qs else None
                    start   = datetime.strptime(qs["start"][0],"%Y-%m-%d") if "start" in qs else None
                    end     = datetime.strptime(qs["end"][0],  "%Y-%m-%d") if "end"   in qs else None
                    msgs    = search_messages(query=q,contact=contact,start_date=start,end_date=end)
                    self.send_json({"messages":msgs,"count":len(msgs)})
                except Exception as e:
                    self.send_json({"error":str(e),"messages":[],"count":0},500)

            elif parsed.path == "/api/conversation":
                try:
                    msg_id = int(qs["msg_id"][0]) if "msg_id" in qs else 0
                    name, msgs = get_conversation(msg_id)
                    self.send_json({"chat_name":name,"messages":msgs,"target_id":msg_id})
                except Exception as e:
                    self.send_json({"error":str(e)},500)

            elif parsed.path == "/api/memories":
                try:
                    self.send_json({"memories":get_memories()})
                except Exception as e:
                    self.send_json({"error":str(e),"memories":[]},500)
            else:
                self.send_response(404); self.end_headers()

if __name__ == "__main__":
    print(f"\n💬 iMessage4Me → http://localhost:{PORT}\n")
    if USE_FLASK:
        app.run(port=PORT, debug=False)
    else:
        print("(Flask not found — using built-in server. Run 'pip3 install flask' for best results)\n")
        HTTPServer(("", PORT), Handler).serve_forever()
