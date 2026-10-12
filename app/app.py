"""Thesis Checker v2 - explainable AI-text + plagiarism checks for whole papers (Kaggle/Colab/CPU)."""
import os, re, json, time, hashlib, html, statistics
import gradio as gr, torch, requests
from rapidfuzz import fuzz

CACHE_FILE = "cache.json"
CACHE = json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}
def save_cache(): json.dump(CACHE, open(CACHE_FILE, "w"))
def md5(s): return hashlib.md5(s.encode()).hexdigest()
esc = html.escape

# ---------- text ----------
def read_file(path):
    p = path.lower()
    if p.endswith(".docx"):
        import docx
        return "\n".join(x.text for x in docx.Document(path).paragraphs)
    if p.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
    return open(path, encoding="utf-8", errors="ignore").read()

def split_refs(text):
    m = list(re.finditer(r"^\s*(references|bibliography|works cited)\s*$", text, re.I | re.M))
    if m and m[-1].start() > len(text) * 0.5: return text[:m[-1].start()], text[m[-1].end():]
    return text, ""

def make_blocks(text, target=150, cap=300):
    blocks, cur, n = [], [], 0
    for u in (l.strip() for l in text.split("\n")):
        if not u: continue
        cur.append(u); n += len(u.split())
        if (n >= target and re.search(r'[.!?"”)]$', u)) or n >= cap:
            blocks.append(" ".join(cur)); cur, n = [], 0
    if cur:
        if blocks and n < 60: blocks[-1] += " " + " ".join(cur)
        else: blocks.append(" ".join(cur))
    return blocks

def sentences(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]

# ---------- AI detectors ----------
class Detector:
    def __init__(self, size, use_edit, use_bino):
        from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSequenceClassification
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        dt = torch.float16 if self.dev == "cuda" else torch.float32
        self.em = None
        if use_edit:
            eid = "CoderBak/editlens_roberta_modelkit"  # community copy of Pangram's open EditLens RoBERTa-large
            self.etok = AutoTokenizer.from_pretrained(eid)
            self.em = AutoModelForSequenceClassification.from_pretrained(eid, torch_dtype=dt).to(self.dev).eval()
        self.obs = None
        if use_bino:
            base = f"Qwen/Qwen2.5-{size}"
            self.tok = AutoTokenizer.from_pretrained(base)
            self.obs = AutoModelForCausalLM.from_pretrained(base, torch_dtype=dt).to(self.dev).eval()
            self.perf = AutoModelForCausalLM.from_pretrained(base + "-Instruct", torch_dtype=dt).to(self.dev).eval()

    @torch.no_grad()
    def edit(self, text):  # 0 = human ... 1 = fully AI (ordinal heads are averaged into one 0-1 score)
        if not self.em: return None
        enc = self.etok(text, return_tensors="pt", truncation=True, max_length=512).to(self.dev)
        lg = self.em(**enc).logits[0].float()
        if lg.numel() == 1: return torch.sigmoid(lg[0]).item()
        p = torch.softmax(lg, -1)
        return float((p * torch.arange(len(p), device=p.device)).sum() / (len(p) - 1))

    @torch.no_grad()
    def bino(self, text):  # Binoculars: lower = more machine-like
        if not self.obs: return None
        enc = self.tok(text, return_tensors="pt", truncation=True, max_length=512).to(self.dev)
        o = self.obs(**enc).logits[0, :-1].float(); p = self.perf(**enc).logits[0, :-1].float()
        ppl = torch.nn.functional.cross_entropy(p, enc.input_ids[0, 1:])
        x = -(torch.softmax(o, -1) * torch.log_softmax(p, -1)).sum(-1).mean()
        return (ppl / x).item()

DET = {}
def get_det(size, ue, ub):
    k = (size, ue, ub)
    if k not in DET: DET.clear(); DET[k] = Detector(size, ue, ub)
    return DET[k]

# ---------- plagiarism / sources ----------
def toks(t): return re.findall(r"[a-z0-9']+", t.lower())
def grams(w, n=8): return {hash(" ".join(w[i:i + n])) for i in range(len(w) - n + 1)}

def pick_queries(block):
    ss = [s for s in sentences(block) if 14 <= len(s.split()) <= 40 and sum(c.isdigit() for c in s) < 5 and '"' not in s]
    ss.sort(key=lambda s: -sum(len(w) > 6 for w in s.split()))
    return [" ".join(s.split()[:12]) for s in ss[:3]]

def infini(q):
    try:
        r = requests.post("https://api.infini-gram.io/", json={"index": "v4_rpj_llama_s4", "query_type": "count", "query": q}, timeout=20).json()
        return [("corpus", f"exact phrase found {r['count']}× in open web corpus (RedPajama)", "")] if r.get("count", 0) > 0 else []
    except Exception: return None

def web(q):
    hits, ok = [], False
    try:
        from ddgs import DDGS
        for r in DDGS().text(f'"{q}"', max_results=5):
            ok = True
            if fuzz.partial_ratio(q.lower(), r["body"].lower()) >= 92: hits.append(("web", r["href"], r["href"]))
    except Exception: pass
    try:
        r = requests.get("https://api.semanticscholar.org/graph/v1/snippet/search", params={"query": q, "limit": 5}, timeout=15)
        if r.ok:
            ok = True
            for d in r.json().get("data", []):
                if fuzz.partial_ratio(q.lower(), d["snippet"]["text"].lower()) >= 92:
                    hits.append(("paper", "Semantic Scholar: " + d["paper"].get("title", "paper"), ""))
    except Exception: pass
    return hits if ok else None

def check_refs(refs_text, limit=60):
    out = []
    for line in [l.strip() for l in refs_text.split("\n") if len(l.strip()) > 30][:limit]:
        try:
            it = requests.get("https://api.crossref.org/works", params={"query.bibliographic": line, "rows": 1}, timeout=15).json()["message"]["items"][0]
            title = (it.get("title") or [""])[0]
            out.append((line, fuzz.partial_ratio(title.lower(), line.lower()) >= 80, title, it.get("DOI", "")))
        except Exception: out.append((line, None, "", ""))
        time.sleep(0.3)
    return out

def doc_issues(blocks):
    full = " ".join(blocks); out = []
    seen = {}
    for s in sentences(full):
        if len(s.split()) >= 8: seen[re.sub(r"\W+", " ", s.lower())] = seen.get(re.sub(r"\W+", " ", s.lower()), 0) + 1
    out += [("Repeated sentence", f"appears {n}×: “{s[:140]}…”") for s, n in seen.items() if n > 1]
    for pat, name in [(r"please confirm|\bTODO\b|\bTBD\b|lorem ipsum|\[insert", "Leftover placeholder"),
                      (r"\b(?:a|an|the) [-–]\s?[a-z]+", "Possible missing word/number"), (r"\.\.(?!\.)", "Double full stop")]:
        out += [(name, f"…{full[max(0, m.start()-50):m.end()+50]}…") for m in re.finditer(pat, full, re.I)]
    return out

# ---------- main ----------
CHIP = {0: ("Low", "#2a9d5b"), 1: ("Medium", "#d9a300"), 2: ("High", "#d64545")}
TECH = re.compile(r"regression|coefficient|p\s*=|elasticity|table \d|hypothes|statistic|equation|ardl|figure \d", re.I)

def run(thesis, extra, use_edit, use_bino, size, hi, mid, sens, calib, use_local, use_infini, use_web, nq, use_refs, use_issues, show, progress=gr.Progress()):
    if not thesis: return "<p>Upload a thesis file first.</p>", ""
    body, refs_text = split_refs(read_file(thesis)); blocks = make_blocks(body)
    B = [{"text": t, "edit": None, "bino": None, "why": [], "ai": 0, "pl": [], "pls": 0} for t in blocks]
    notes = []
    if use_edit or use_bino:
        det = get_det(size, use_edit, use_bino)
        def sc(t):
            k = md5(f"{size}{use_edit}{use_bino}{t}")
            if k not in CACHE: CACHE[k] = {"e": det.edit(t), "b": det.bino(t)}
            return CACHE[k]
        for i, b in enumerate(B):
            progress((i, len(B)), desc="AI scan"); r = sc(b["text"]); b["edit"], b["bino"] = r["e"], r["b"]
            if i % 10 == 0: save_cache()
        hb = [sc(t) for t in make_blocks(calib)] if calib and calib.strip() else []
        if hb and use_edit:
            hs = [x["e"] for x in hb]; hi = max(hi, max(hs)); mid = min(mid, hi)
            notes.append(f"Your known-human sample scored up to {max(hs):.2f} on the AI scale, so the High threshold is {hi:.2f}.")
        base = [x["b"] for x in hb] if hb and use_bino else [b["bino"] for b in B if b["bino"] is not None]
        mu, sd = (statistics.mean(base), statistics.pstdev(base) or 0.01) if base else (0, 1)
        notes.append("Binoculars baseline: " + ("your known-human sample." if hb else "this paper itself (weaker, since it assumes most of the paper is human)."))
        for b in B:
            pts, n = 0, 0
            if b["edit"] is not None:
                n += 1; e = b["edit"]
                band = "high" if e >= hi else "medium" if e >= mid else "low"
                pts += 2 if e >= hi else 1 if e >= mid else 0
                b["why"].append(f"<b>EditLens AI score {e:.2f}</b> → {band} (High ≥ {hi:.2f}, Medium ≥ {mid:.2f}). This model was trained to separate human, AI-edited and AI-written text, so heavy AI polishing also raises it.")
            if b["bino"] is not None:
                n += 1; z = (b["bino"] - mu) / sd; fl = z < -sens; pts += 1 if fl else 0
                b["why"].append(f"<b>Binoculars {b['bino']:.3f}</b> (z = {z:+.2f}) → " + ("more predictable to language models than the baseline, so it looks machine-like." if fl else "within the normal range of the baseline.") + " Lower = more machine-like.")
            if TECH.search(b["text"]) or sum(c.isdigit() for c in b["text"]) / max(len(b["text"]), 1) > .04:
                b["why"].append("⚠ Technical/formulaic text (statistics, tables, definitions). Detectors flag this kind of writing even when it is human, so treat a flag here with extra caution.")
            b["ai"] = 2 if pts >= 3 or (n == 1 and pts >= 2) else 1 if pts >= 1 else 0
            if b["ai"] == 0: b["why"].append("No detector crossed its threshold.")
    if use_local and extra:
        rg = {os.path.basename(p): grams(toks(read_file(p))) for p in extra}
        for b in B:
            g = grams(toks(b["text"]))
            for n, s in rg.items():
                f = len(g & s) / max(1, len(g))
                if f > .05: b["pl"].append(("local", f"{f:.0%} of this block's 8-word sequences also appear in <b>{esc(n)}</b>", "")); b["pls"] = max(b["pls"], 2 if f > .3 else 1)
    if use_infini or use_web:
        cands = [pick_queries(b["text"]) for b in B]
        qs = [(i, c[r]) for r in range(3) for i, c in enumerate(cands) if r < len(c)][:int(nq)]
        ok = fail = 0
        for j, (i, q) in enumerate(qs):
            progress((j, len(qs)), desc="Source check")
            for name, on, fn in (("i", use_infini, infini), ("w", use_web, web)):
                if not on: continue
                k = name + md5(q)
                if k not in CACHE:
                    h = fn(q)
                    if h is not None: CACHE[k] = h
                    if name == "w": time.sleep(1.5)
                h = CACHE.get(k)
                if h is None: fail += 1; continue
                ok += 1
                for kind, label, url in h: B[i]["pl"].append((kind, esc(label) if kind != "local" else label, url)); B[i]["pls"] = max(B[i]["pls"], 1 + (len(B[i]["pl"]) > 1))
        notes.append(f"Source search: {ok} lookups succeeded, {fail} failed or were throttled (failures are not 'clean' results). Only {len(qs)} sampled sentences were checked.")
    save_cache()
    refs = check_refs(refs_text) if use_refs and refs_text else []
    issues = doc_issues(blocks) if use_issues else []
    # ---- render ----
    def card(i, b):
        sev = max(b["ai"], b["pls"]); lab, col = CHIP[sev]
        why = "".join(f"<li>{w}</li>" for w in b["why"])
        if b["pl"]:
            why += "<li><b>Possible overlap with other sources</b><ul>" + "".join(f"<li>{('<a href=%s target=_blank>%s</a>' % (esc(u), l)) if u else l}</li>" for _, l, u in dict.fromkeys(b["pl"])) + "</ul>Exact matches of common phrases can be harmless; open the source and judge whether it is copied or properly cited.</li>"
        return (f"<details class='blk'><summary><span class='chip' style='background:{col}'>{lab}</span> "
                f"<b>#{i+1}</b> <span class='pv'>{esc(b['text'][:120])}…</span></summary><div class='bd'><p>{esc(b['text'])}</p>"
                f"<p><b>Why this rating</b></p><ul>{why}</ul></div></details>")
    keep = [(i, b) for i, b in enumerate(B) if show == "All blocks" or (show == "Medium + High" and max(b["ai"], b["pls"]) >= 1) or max(b["ai"], b["pls"]) == 2]
    cards = "".join(card(i, b) for i, b in keep) or "<p>Nothing to show at this filter.</p>"
    extra_html = ""
    if issues:
        extra_html += "<details class='blk'><summary><span class='chip' style='background:#6b7cff'>Paper</span> <b>Writing &amp; consistency issues</b> (%d)</summary><div class='bd'><p>Things a reader or supervisor may notice. Not related to AI or plagiarism.</p><ul>%s</ul></div></details>" % (len(issues), "".join(f"<li><b>{a}:</b> {esc(d)}</li>" for a, d in issues))
    if refs:
        bad = [r for r in refs if r[1] is False]
        extra_html += "<details class='blk'><summary><span class='chip' style='background:#6b7cff'>Refs</span> <b>Reference check</b> (%d of %d not matched)</summary><div class='bd'><p>Each reference was looked up in Crossref. “Not matched” can mean a book, report or local publication that Crossref lacks, so check manually; a fabricated citation would also appear here.</p><ul>%s</ul></div></details>" % (len(bad), len(refs), "".join(f"<li>{'✅' if ok else '❓' if ok is None else '⚠️ not matched'} {esc(l[:160])}" + (f" → <a href='https://doi.org/{d}' target=_blank>{esc(t[:70])}</a>" if ok and d else "") + "</li>" for l, ok, t, d in refs))
    tw = sum(len(b["text"].split()) for b in B)
    cnt = lambda s: sum(1 for b in B if max(b["ai"], b["pls"]) == s)
    summ = (f"<div class='cards'><div><b>{len(B)}</b><br>blocks · {tw:,} words</div><div style='border-color:#d64545'><b>{cnt(2)}</b><br>High</div>"
            f"<div style='border-color:#d9a300'><b>{cnt(1)}</b><br>Medium</div><div style='border-color:#2a9d5b'><b>{cnt(0)}</b><br>Low</div></div>"
            "<p><small>" + " ".join(esc(n) for n in notes) + " Ratings are guidance for revising, not proof of AI use or plagiarism.</small></p>")
    return summ, extra_html + cards

CSS = """.cards{display:flex;gap:12px;flex-wrap:wrap}.cards div{flex:1;min-width:120px;padding:12px;border:2px solid #8886;border-radius:12px;text-align:center}
.cards b{font-size:1.6em}.blk{border:1px solid #8885;border-radius:10px;margin:8px 0;padding:6px 12px}.blk summary{cursor:pointer;padding:6px 0}
.chip{color:#fff;border-radius:999px;padding:2px 10px;font-size:.8em;margin-right:6px}.pv{opacity:.7}.bd{padding:4px 0 10px}.bd p{line-height:1.6}"""

HOW = """**What the checker does:** it splits the paper (without the reference list) into blocks of 150–300 words and rates each block Low / Medium / High.

- **EditLens (main AI detector):** an open model from Pangram trained on human, AI-edited and AI-written text, giving a 0–1 score. Heavily AI-polished text scores higher.
- **Binoculars (second opinion):** two language models read the text; if it is unusually predictable to them, it looks machine-written. Lower score = more machine-like.
- **High** needs strong evidence (e.g. both detectors agree). **Medium** means one signal. Formulaic sections (methods, tables, definitions) get a caution note, because detectors often flag them wrongly.
- **Plagiarism:** (a) your uploaded sources, via 8-word overlap; (b) exact-phrase lookup in an open web corpus (infini-gram); (c) web + paper-snippet search. Only a sample of sentences is checked, and source-search failures are reported.
- **Reference check:** each reference is looked up in Crossref to catch invented or mistyped citations.
- **Calibration:** pasting a few paragraphs the author definitely wrote raises the thresholds so his normal style is not flagged. Do this if you can.

**Limits:** no detector is proof. Do not use these results to accuse anyone; use them to decide what to rewrite and cite. Open Pangram models are licensed for non-commercial use and the authors say not to use them to enforce AI policies. Source checks send sentences to outside services; switch them off for private work."""

with gr.Blocks(title="Thesis Checker", theme=gr.themes.Soft(), css=CSS) as demo:
    gr.Markdown("# 🎓 Thesis Checker\nAI-text detection, plagiarism and reference checks for full papers. **Recommended settings are already selected.**")
    with gr.Accordion("How this works & its limits (read first)", open=False): gr.Markdown(HOW)
    with gr.Row():
        thesis = gr.File(label="Thesis (.docx / .pdf / .txt)", type="filepath")
        extra = gr.File(label="Optional: source papers to compare against", type="filepath", file_count="multiple")
    with gr.Accordion("Settings", open=False):
        gr.Markdown("### AI detection")
        with gr.Row():
            use_edit = gr.Checkbox(True, label="EditLens detector", info="Main detector. Distinguishes human / AI-edited / AI-written. Recommended: on.")
            use_bino = gr.Checkbox(True, label="Binoculars detector", info="Second opinion; agreement between both raises confidence. Recommended: on.")
            size = gr.Dropdown(["0.5B", "1.5B", "3B"], value="1.5B" if torch.cuda.is_available() else "0.5B", label="Binoculars model size", info="Bigger = more accurate but slower. 1.5B on GPU, 0.5B on CPU.")
        with gr.Row():
            hi = gr.Slider(0.3, 0.95, 0.6, step=0.05, label="High threshold (EditLens)", info="Scores above this are High. Raise it to flag less.")
            mid = gr.Slider(0.1, 0.8, 0.35, step=0.05, label="Medium threshold (EditLens)", info="Scores above this are Medium.")
            sens = gr.Slider(0.2, 3, 1.0, step=0.1, label="Binoculars sensitivity", info="Flags blocks this many standard deviations below baseline. Higher = flags less.")
        calib = gr.Textbox(lines=3, label="Known-human sample (strongly recommended)", info="Paste a few paragraphs the author definitely wrote himself, e.g. from an older paper. Used to calibrate both detectors.")
        gr.Markdown("### Plagiarism & checks")
        with gr.Row():
            use_local = gr.Checkbox(True, label="Compare with uploaded sources", info="Needs source files above.")
            use_infini = gr.Checkbox(True, label="Open web corpus (infini-gram)", info="Exact-phrase lookup. Fast and not rate-limited like search engines.")
            use_web = gr.Checkbox(True, label="Web + paper search", info="DuckDuckGo and Semantic Scholar. May be throttled.")
        with gr.Row():
            nq = gr.Slider(10, 1000, 150, step=10, label="Max sentences to check online", info="More = better coverage but slower and more throttling.")
            use_refs = gr.Checkbox(True, label="Verify references (Crossref)", info="Catches invented or mistyped citations.")
            use_issues = gr.Checkbox(True, label="Writing & consistency checks", info="Repeated sentences, leftover placeholders, missing words.")
        gr.Markdown("<small>Privacy: online checks send short phrases of the paper to outside services. Turn them off for unpublished work you must keep private.</small>")
    show = gr.Radio(["All blocks", "Medium + High", "High only"], value="All blocks", label="Show")
    btn = gr.Button("Run check", variant="primary", size="lg")
    summ, out = gr.HTML(), gr.HTML()
    btn.click(run, [thesis, extra, use_edit, use_bino, size, hi, mid, sens, calib, use_local, use_infini, use_web, nq, use_refs, use_issues, show], [summ, out])

if __name__ == "__main__":
    pw = os.environ.get("APP_PASS")
    demo.queue().launch(share=True, auth=("user", pw) if pw else None)
