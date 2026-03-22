"""
Blockchain Demo — Single File (Python + HTML)
=============================================
Run:   pip install flask
       python blockchain.py

Opens automatically at http://localhost:5000
"""

from flask import Flask, jsonify, request
import hashlib, threading, webbrowser, time

app = Flask(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
DIFFICULTY = 2
Z64 = '0' * 64

TX_DEFAULT = [
    'Alice  ->  Bob   : 2.50 BTC',
    'Bob    ->  Carol : 1.00 BTC',
    'Carol  ->  Dave  : 0.80 BTC',
    'Dave   ->  Eve   : 3.20 BTC',
    'Eve    ->  Alice : 0.50 BTC',
]
TS_DEFAULT = [
    '2024-01-15 09:00:01',
    '2024-01-15 09:02:13',
    '2024-01-15 09:05:47',
    '2024-01-15 09:08:22',
    '2024-01-15 09:11:59',
]

chain = []

def sha256(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def compute_hash(bid, nonce, data, ts, prev):
    return sha256(f"{bid}|{nonce}|{data}|{ts}|{prev}")

def pfx():
    return '0' * DIFFICULTY

def block_valid(b, prev_hash):
    rc = compute_hash(b['id'], b['nonce'], b['data'], b['ts'], b['prev'])
    return (b['hash'] == rc and b['hash'].startswith(pfx()) and
            (b['prev'] == Z64 if b['id'] == 1 else b['prev'] == prev_hash))

def init_chain():
    global chain
    chain = []
    prev = Z64
    for i in range(5):
        h = compute_hash(i+1, 0, TX_DEFAULT[i], TS_DEFAULT[i], prev)
        b = {'id': i+1, 'nonce': 0, 'data': TX_DEFAULT[i], 'ts': TS_DEFAULT[i], 'prev': prev, 'hash': h}
        chain.append(b)
        prev = h

init_chain()

def chain_with_validity():
    return [{**b, 'valid': block_valid(b, chain[i-1]['hash'] if i > 0 else Z64)}
            for i, b in enumerate(chain)]

# ── API Routes ────────────────────────────────────────────────────────────────
@app.route('/api/chain')
def get_chain():
    return jsonify(chain_with_validity())

@app.route('/api/reset', methods=['POST'])
def reset():
    init_chain()
    return jsonify({'status': 'ok'})

@app.route('/api/update/<int:bid>', methods=['POST'])
def update_block(bid):
    if bid < 1 or bid > 5: return jsonify({'error': 'bad id'}), 400
    body = request.get_json()
    b = chain[bid-1]
    if 'nonce' in body:
        try: b['nonce'] = int(body['nonce'])
        except: b['nonce'] = 0
    if 'data' in body: b['data'] = str(body['data'])
    if 'ts'   in body: b['ts']   = str(body['ts'])
    for i in range(bid-1, 5):
        if i > 0: chain[i]['prev'] = chain[i-1]['hash']
        chain[i]['hash'] = compute_hash(chain[i]['id'], chain[i]['nonce'],
                                        chain[i]['data'], chain[i]['ts'], chain[i]['prev'])
    return jsonify(chain_with_validity())

@app.route('/api/mine/<int:bid>', methods=['POST'])
def mine_block(bid):
    if bid < 1 or bid > 5: return jsonify({'error': 'bad id'}), 400
    b = chain[bid-1]; p = pfx()
    for n in range(3_000_001):
        h = compute_hash(b['id'], n, b['data'], b['ts'], b['prev'])
        if h.startswith(p):
            b['nonce'] = n; b['hash'] = h
            for i in range(bid, 5):
                chain[i]['prev'] = chain[i-1]['hash']
                chain[i]['hash'] = compute_hash(chain[i]['id'], chain[i]['nonce'],
                                                chain[i]['data'], chain[i]['ts'], chain[i]['prev'])
            return jsonify({'status': 'mined', 'nonce': n, 'hash': h, 'chain': chain_with_validity()})
    return jsonify({'status': 'failed', 'message': 'Stopped at 3M tries'})

@app.route('/api/verify')
def verify_chain():
    p = pfx(); report = []; all_ok = True
    for i, b in enumerate(chain):
        ph = chain[i-1]['hash'] if i > 0 else Z64
        rc = compute_hash(b['id'], b['nonce'], b['data'], b['ts'], b['prev'])
        hm = b['hash'] == rc; hv = b['hash'].startswith(p)
        pv = (b['prev'] == Z64) if i == 0 else (b['prev'] == chain[i-1]['hash'])
        ok = hm and hv and pv
        if not ok: all_ok = False
        report.append({'id': b['id'], 'data': b['data'], 'ts': b['ts'], 'nonce': b['nonce'],
                       'stored_hash': b['hash'], 'recomputed_hash': rc,
                       'hash_match': hm, 'hash_valid': hv, 'prev_valid': pv, 'valid': ok})
    return jsonify({'all_valid': all_ok, 'blocks': report})

# ── Embedded HTML ─────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blockchain Demo</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#07090f; --panel:#0c1020; --card:#101828; --border:#1a2740;
  --accent:#00cfff; --green:#00ff88; --red:#ff3d6b; --orange:#ffaa00;
  --purple:#8b5cf6; --text:#b8cce0; --dim:#3a5270; --mono:'Share Tech Mono',monospace;
  --sans:'Rajdhani',sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:var(--mono);min-height:100vh;overflow-x:hidden}

body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,207,255,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,207,255,.025) 1px,transparent 1px);
  background-size:48px 48px;pointer-events:none;z-index:0}

/* Glow orbs */
body::after{content:'';position:fixed;inset:0;
  background:radial-gradient(ellipse 600px 400px at 10% 20%,rgba(139,92,246,.06),transparent),
             radial-gradient(ellipse 500px 300px at 90% 80%,rgba(0,207,255,.05),transparent);
  pointer-events:none;z-index:0}

header{position:relative;z-index:2;padding:22px 36px;
  border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;
  background:rgba(7,9,15,.8);backdrop-filter:blur(10px)}

.logo{display:flex;align-items:center;gap:14px}
.logo-hex{width:40px;height:40px;background:linear-gradient(135deg,var(--accent),var(--purple));
  clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
  display:flex;align-items:center;justify-content:center;font-size:16px}
h1{font-family:var(--sans);font-size:24px;font-weight:700;letter-spacing:4px;
  text-transform:uppercase;
  background:linear-gradient(90deg,var(--accent) 0%,var(--purple) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}

.hdr-right{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:10px;
  padding:5px 12px;border-radius:20px;border:1px solid var(--border);color:var(--dim);
  letter-spacing:1px;transition:all .3s}
.badge.ok{border-color:rgba(0,255,136,.4);color:var(--green)}
.badge.err{border-color:rgba(255,61,107,.4);color:var(--red)}
.badge-dot{width:6px;height:6px;border-radius:50%;background:currentColor}
.badge.ok .badge-dot{animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

.info-chips{display:flex;gap:8px}
.chip{font-size:10px;padding:4px 10px;border-radius:4px;
  background:rgba(255,255,255,.03);border:1px solid var(--border);
  color:var(--dim);letter-spacing:1px}
.chip strong{color:var(--accent)}

/* Actions */
.actions{position:relative;z-index:1;padding:14px 36px;
  display:flex;gap:10px;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.btn{font-family:var(--mono);font-size:11px;padding:8px 22px;
  border-radius:6px;cursor:pointer;border:1px solid;letter-spacing:1.5px;transition:all .2s}
.btn-reset{background:transparent;border-color:var(--border);color:var(--dim)}
.btn-reset:hover{border-color:var(--accent);color:var(--accent);box-shadow:0 0 12px rgba(0,207,255,.15)}
.btn-verify{background:rgba(0,255,136,.06);border-color:rgba(0,255,136,.3);color:var(--green)}
.btn-verify:hover{background:rgba(0,255,136,.14);box-shadow:0 0 12px rgba(0,255,136,.2)}

/* Chain */
.chain-scroll{position:relative;z-index:1;overflow-x:auto;padding:30px 36px 10px}
.chain{display:flex;align-items:flex-start}
.arrow-col{display:flex;align-items:center;padding:0 4px;margin-top:106px}
.arrow-body{position:relative;width:30px;height:2px;
  background:linear-gradient(90deg,var(--border),var(--accent))}
.arrow-body::after{content:'▶';position:absolute;right:-6px;top:-7px;
  font-size:9px;color:var(--accent)}

/* Block */
.block{width:218px;flex-shrink:0;background:var(--card);
  border:1px solid var(--border);border-radius:14px;overflow:hidden;
  transition:border-color .35s,box-shadow .35s}
.block.valid{border-color:rgba(0,255,136,.35);box-shadow:0 0 24px rgba(0,255,136,.07)}
.block.invalid{border-color:rgba(255,61,107,.35);box-shadow:0 0 24px rgba(255,61,107,.07)}

.bhead{padding:10px 14px;display:flex;justify-content:space-between;align-items:center;
  border-bottom:1px solid var(--border);background:rgba(0,0,0,.3)}
.bnum{font-family:var(--sans);font-size:13px;font-weight:700;
  letter-spacing:2px;color:var(--accent)}
.led{width:10px;height:10px;border-radius:50%;transition:all .3s}
.led.ok{background:var(--green);box-shadow:0 0 10px var(--green)}
.led.bad{background:var(--red);box-shadow:0 0 10px var(--red)}

.bbody{padding:12px 14px;display:flex;flex-direction:column;gap:9px}
.field label{display:block;font-size:9px;letter-spacing:2px;
  color:var(--dim);text-transform:uppercase;margin-bottom:3px}
.field input,.field textarea{width:100%;padding:6px 8px;
  background:rgba(0,0,0,.35);border:1px solid var(--border);border-radius:5px;
  color:var(--text);font-family:var(--mono);font-size:10px;outline:none;transition:border-color .2s}
.field input:focus,.field textarea:focus{border-color:var(--accent)}
.field input[readonly]{color:var(--dim);cursor:default}
.field textarea{height:56px;resize:none}

.c-nonce{color:var(--orange)!important}
.c-hash{color:var(--green)!important;font-size:9px!important}
.c-bad{color:var(--red)!important;font-size:9px!important}
.c-prev{color:var(--accent)!important;font-size:9px!important}

.mine-btn{width:100%;padding:9px;margin-top:2px;
  background:linear-gradient(135deg,var(--purple),#5b3db0);
  border:none;border-radius:7px;color:#fff;
  font-family:var(--mono);font-size:12px;letter-spacing:1px;
  cursor:pointer;transition:all .2s}
.mine-btn:hover:not(:disabled){background:linear-gradient(135deg,#a47ef8,var(--purple));
  box-shadow:0 0 18px rgba(139,92,246,.45)}
.mine-btn:disabled{background:var(--border);color:var(--dim);cursor:not-allowed}

.mining-lbl{display:none;text-align:center;font-size:10px;
  color:var(--orange);letter-spacing:1px}
.mining-lbl.on{display:block;animation:blink .7s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}

.prog-bar{height:2px;background:var(--border);border-radius:2px;overflow:hidden;display:none}
.prog-bar.on{display:block}
.prog-fill{height:100%;width:30%;
  background:linear-gradient(90deg,transparent,var(--accent),var(--purple),transparent);
  background-size:200%;animation:sweep 1.2s linear infinite}
@keyframes sweep{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* Log */
.log-wrap{position:relative;z-index:1;margin:16px 36px 40px;
  background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden}
.log-hdr{padding:11px 18px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:10px;
  font-family:var(--sans);font-size:13px;font-weight:700;
  letter-spacing:3px;color:var(--dim)}
.log-hdr::before{content:'';width:6px;height:6px;border-radius:50%;
  background:var(--accent);box-shadow:0 0 8px var(--accent)}
.log-body{padding:12px 18px;font-size:11px;line-height:2;
  max-height:240px;overflow-y:auto;color:var(--dim)}
.log-body::-webkit-scrollbar{width:3px}
.log-body::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.lo{color:var(--green)}.le{color:var(--red)}.li{color:var(--accent)}.lw{color:var(--orange)}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-hex">⛓</div>
    <h1>Blockchain</h1>
  </div>
  <div class="hdr-right">
    <div class="badge err" id="badge">
      <span class="badge-dot"></span>
      <span id="badgeTxt">Connecting...</span>
    </div>
    <div class="info-chips">
      <div class="chip">DIFFICULTY <strong>2</strong></div>
      <div class="chip">BLOCKS <strong>5</strong></div>
    </div>
  </div>
</header>

<div class="actions">
  <button class="btn btn-reset"  onclick="resetChain()">↺ &nbsp;RESET</button>
  <button class="btn btn-verify" onclick="verifyChain()">✓ &nbsp;VERIFY CHAIN</button>
</div>

<div class="chain-scroll">
  <div class="chain" id="chain"></div>
</div>

<div class="log-wrap">
  <div class="log-hdr">VERIFICATION LOG</div>
  <div class="log-body" id="log"><span class="li">Initializing...</span></div>
</div>

<script>
const API = '/api';
let chainData = [];

// ── Render ────────────────────────────────────────────────────────────────────
function renderChain() {
  const el = document.getElementById('chain');
  el.innerHTML = '';
  chainData.forEach((b, i) => {
    if (i > 0) {
      const a = document.createElement('div');
      a.className = 'arrow-col';
      a.innerHTML = '<div class="arrow-body"></div>';
      el.appendChild(a);
    }
    el.appendChild(buildCard(b));
  });
}

function buildCard(b) {
  const v = b.valid;
  const d = document.createElement('div');
  d.className = `block ${v ? 'valid' : 'invalid'}`;
  d.id = `B${b.id}`;
  d.innerHTML = `
    <div class="bhead">
      <span class="bnum">BLOCK #${b.id}</span>
      <div class="led ${v?'ok':'bad'}" id="L${b.id}"></div>
    </div>
    <div class="bbody">
      <div class="field">
        <label>Nonce</label>
        <input type="number" class="c-nonce" id="N${b.id}" value="${b.nonce}"
               oninput="upd(${b.id},'nonce',this.value)">
      </div>
      <div class="field">
        <label>Data</label>
        <textarea id="DA${b.id}" oninput="upd(${b.id},'data',this.value)">${b.data}</textarea>
      </div>
      <div class="field">
        <label>Timestamp</label>
        <input type="text" id="Ti${b.id}" value="${b.ts}"
               oninput="upd(${b.id},'ts',this.value)">
      </div>
      <div class="field">
        <label>Prev Hash</label>
        <input class="c-prev" id="PV${b.id}" value="${b.prev.slice(0,26)}..." readonly>
      </div>
      <div class="field">
        <label>Hash</label>
        <input class="${v?'c-hash':'c-bad'}" id="HA${b.id}"
               value="${b.hash.slice(0,26)}..." readonly>
      </div>
      <div class="prog-bar" id="PG${b.id}"><div class="prog-fill"></div></div>
      <div class="mining-lbl" id="ML${b.id}">⛏ MINING...</div>
      <button class="mine-btn" id="MB${b.id}" onclick="mineBlock(${b.id})">⛏ &nbsp;MINE</button>
    </div>`;
  return d;
}

function refreshCard(b) {
  const v = b.valid;
  const card = document.getElementById(`B${b.id}`); if (!card) return;
  card.className = `block ${v?'valid':'invalid'}`;
  document.getElementById(`L${b.id}`).className = `led ${v?'ok':'bad'}`;
  const he = document.getElementById(`HA${b.id}`);
  he.className = v ? 'c-hash' : 'c-bad';
  he.value = b.hash.slice(0,26)+'...';
  document.getElementById(`PV${b.id}`).value = b.prev.slice(0,26)+'...';
  document.getElementById(`N${b.id}`).value  = b.nonce;
}

// ── API ───────────────────────────────────────────────────────────────────────
async function loadChain() {
  const r = await fetch(`${API}/chain`);
  chainData = await r.json();
  renderChain();
}

let updTimer = null;
function upd(id, field, value) {
  clearTimeout(updTimer);
  updTimer = setTimeout(async () => {
    const body = {}; body[field] = field==='nonce' ? (parseInt(value)||0) : value;
    const r = await fetch(`${API}/update/${id}`,
      {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    chainData = await r.json();
    chainData.forEach(refreshCard);
  }, 220);
}

async function mineBlock(id) {
  const btn=document.getElementById(`MB${id}`),
        ml =document.getElementById(`ML${id}`),
        pg =document.getElementById(`PG${id}`);
  btn.disabled=true; ml.className='mining-lbl on'; pg.className='prog-bar on';
  log(`Block #${id} — mining...`, 'w');
  const r    = await fetch(`${API}/mine/${id}`, {method:'POST'});
  const data = await r.json();
  btn.disabled=false; ml.className='mining-lbl'; pg.className='prog-bar';
  if (data.status==='mined') {
    chainData = data.chain; chainData.forEach(refreshCard);
    log(`Block #${id} mined!  nonce=${data.nonce}  hash=${data.hash.slice(0,20)}...`, 'o');
  } else { log(`Block #${id}: ${data.message}`, 'e'); }
}

async function verifyChain() {
  clearLog();
  const r    = await fetch(`${API}/verify`);
  const data = await r.json();
  log('=== CHAIN VERIFICATION ===', 'i');
  data.blocks.forEach(b => {
    log('', ''); log(`Block #${b.id}`, 'w');
    log(`  Data      : ${b.data}`, '');
    log(`  Timestamp : ${b.ts}`, 'i');
    log(`  Nonce     : ${b.nonce}`, '');
    log(`  Stored    : ${b.stored_hash.slice(0,30)}...`, '');
    log(`  Recomputed: ${b.recomputed_hash.slice(0,30)}...`, '');
    if (!b.hash_match)      log('  [FAIL] Hash mismatch — data TAMPERED!', 'e');
    else if (!b.hash_valid) log('  [FAIL] Not mined — no leading zeros', 'e');
    else                    log('  [OK] Hash valid ✓', 'o');
    if (b.id===1)           log('  [OK] Genesis block — prev = 0x0000...', 'o');
    else if (!b.prev_valid) log(`  [FAIL] Prev-hash broken at Block #${b.id}`, 'e');
    else                    log(`  [OK] Prev-hash links to Block #${b.id-1}`, 'o');
    log(`  Miner     : 0x${b.stored_hash.slice(0,10).toUpperCase()} [verified]`, 'o');
  });
  log('', ''); log('=========================', 'i');
  log(data.all_valid ? '  ✓ VALID — All 5 blocks passed!' : '  ✗ INVALID — Tampering detected!',
      data.all_valid ? 'o' : 'e');
  log('=========================', 'i');
}

async function resetChain() {
  await fetch(`${API}/reset`, {method:'POST'});
  await loadChain(); clearLog();
  log('Chain reset. Mine each block, then Verify.', 'i');
}

function log(msg, t) {
  const el=document.getElementById('log');
  const d=document.createElement('div');
  const cls={o:'lo',e:'le',i:'li',w:'lw'}[t]||'';
  if(cls) d.className=cls; d.textContent=msg; el.appendChild(d); el.scrollTop=el.scrollHeight;
}
function clearLog(){ document.getElementById('log').innerHTML=''; }

// ── Init ──────────────────────────────────────────────────────────────────────
(async()=>{
  const badge=document.getElementById('badge'), txt=document.getElementById('badgeTxt');
  try {
    await loadChain();
    badge.className='badge ok'; txt.textContent='Python Server • Live';
    clearLog(); log('Connected to Python backend. Ready!', 'o');
  } catch(e) {
    badge.className='badge err'; txt.textContent='Server Error';
    log('Failed to connect to Python backend.', 'e');
  }
})();
</script>
</body>
</html>"""

@app.route('/')
def index():
    return HTML

# ── Launch ────────────────────────────────────────────────────────────────────
def open_browser():
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("=" * 52)
    print("  ⛓  Blockchain Demo")
    print("=" * 52)
    print("  Install : pip install flask")
    print("  Opening : http://localhost:5000")
    print("  Stop    : Ctrl+C")
    print("=" * 52)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, port=5000)
