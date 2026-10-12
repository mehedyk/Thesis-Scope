"""Thesis checker: AI-text detection (Binoculars + RoBERTa) and plagiarism (local + web).
Runs on Kaggle/Colab (GPU) or CPU. Results are cached in cache.json so re-runs only scan changed text."""
import os, re, json, time, hashlib, html, statistics
import gradio as gr
import torch
from rapidfuzz import fuzz

CACHE_FILE = "cache.json"
CACHE = json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}
def save_cache(): json.dump(CACHE, open(CACHE_FILE, "w"))
def md5(s): return hashlib.md5(s.encode()).hexdigest()

# ---------- text handling ----------
def read_file(path):
    p = path.lower()
    if p.endswith(".docx"):
        import docx
        return "\n".join(x.text for x in docx.Document(path).paragraphs)
    if p.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(path).pages)
    return open(path, encoding="utf-8", errors="ignore").read()

def strip_refs(text):
    m = list(re.finditer(r"^\s*(references|bibliography|works cited)\s*$", text, re.I | re.M))
    return text[:m[-1].start()] if m and m[-1].start() > len(text) * 0.5 else text

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

# ---------- AI detection ----------
class Detector:
    def __init__(self, size, use_rob):
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        self.dev = "cuda" if torch.cuda.is_available() else "cpu"
        dt = torch.float16 if self.dev == "cuda" else torch.float32
        base = f"Qwen/Qwen2.5-{size}"
        self.tok = AutoTokenizer.from_pretrained(base)
        self.obs = AutoModelForCausalLM.from_pretrained(base, torch_dtype=dt).to(self.dev).eval()
        self.perf = AutoModelForCausalLM.from_pretrained(base + "-Instruct", torch_dtype=dt).to(self.dev).eval()
        self.rob = pipeline("text-classification", model="Hello-SimpleAI/chatgpt-detector-roberta",
                            device=0 if self.dev == "cuda" else -1, top_k=None) if use_rob else None

    @torch.no_grad()
    def bino(self, text):  # Binoculars: lower score = more machine-like
        enc = self.tok(text, return_tensors="pt", truncation=True, max_length=512).to(self.dev)
        o = self.obs(**enc).logits[0, :-1].float(); p = self.perf(**enc).logits[0, :-1].float()
        y = enc.input_ids[0, 1:]
        ppl = torch.nn.functional.cross_entropy(p, y)
        x = -(torch.softmax(o, -1) * torch.log_softmax(p, -1)).sum(-1).mean()
        return (ppl / x).item()

    def roberta(self, text):
        if not self.rob: return None
        r = self.rob(text, truncation=True, max_length=512)
        r = r[0] if isinstance(r[0], list) else r
        return max((d["score"] for d in r if d["label"].lower() in ("chatgpt", "ai", "fake", "label_1")), default=None)

DET = {}
def get_det(size, use_rob):
    if (size, use_rob) not in DET: DET.clear(); DET[(size, use_rob)] = Detector(size, use_rob)
    return DET[(size, use_rob)]

# ---------- plagiarism ----------
def toks(t): return re.findall(r"[a-z0-9']+", t.lower())
def grams(w, n=8): return {hash(" ".join(w[i:i + n])) for i in range(len(w) - n + 1)}

def pick_queries(block):
    ss = [s for s in re.split(r"(?<=[.!?])\s+", block) if 14 <= len(s.split()) <= 40
          and sum(c.isdigit() for c in s) < 5 and '"' not in s]
    ss.sort(key=lambda s: -sum(len(w) > 6 for w in s.split()))
    return [" ".join(s.split()[:12]) for s in ss[:3]]

def web_hits(q):
    hits, ok = [], False
    try:
        from ddgs import DDGS
        for r in DDGS().text(f'"{q}"', max_results=5):
            ok = True
            if fuzz.partial_ratio(q.lower(), r["body"].lower()) >= 92: hits.append(r["href"])
    except Exception: pass
    try:
        import requests
        r = requests.get("https://api.semanticscholar.org/graph/v1/snippet/search",
                         params={"query": q, "limit": 5}, timeout=15)
        if r.ok:
            ok = True
            for d in r.json().get("data", []):
                if fuzz.partial_ratio(q.lower(), d["snippet"]["text"].lower()) >= 92:
                    hits.append("S2: " + d["paper"].get("title", "paper"))
    except Exception: pass
    return hits if ok else None

# ---------- main ----------
def run(thesis, refs, use_ai, use_rob, size, use_local, use_web, nq, calib, sens, progress=gr.Progress()):
    if not thesis: return "Upload a thesis file first.", ""
    blocks = make_blocks(strip_refs(read_file(thesis)))
    ai, flag = [None] * len(blocks), [False] * len(blocks)
    if use_ai:
        det = get_det(size, use_rob)
        def score(t):
            k = md5(f"{size}{use_rob}{t}")
            if k not in CACHE: CACHE[k] = {"b": det.bino(t), "r": det.roberta(t)}
            return CACHE[k]
        for i, b in enumerate(blocks):
            progress((i, len(blocks)), desc="AI scan"); ai[i] = score(b)
            if i % 10 == 0: save_cache()
        base = [score(b)["b"] for b in make_blocks(calib)] if calib and calib.strip() else [a["b"] for a in ai]
        mu, sd = statistics.mean(base), (statistics.pstdev(base) or 0.01)
        flag = [a["b"] < mu - sens * sd for a in ai]
    pl = [[] for _ in blocks]
    if use_local and refs:
        rg = {os.path.basename(p): grams(toks(read_file(p))) for p in refs}
        for i, b in enumerate(blocks):
            g = grams(toks(b))
            for n, s in rg.items():
                f = len(g & s) / max(1, len(g))
                if f > 0.05: pl[i].append(f"{n} ({f:.0%})")
    if use_web:
        cands = [pick_queries(b) for b in blocks]
        qs = [(i, c[r]) for r in range(3) for i, c in enumerate(cands) if r < len(c)][:int(nq)]
        for j, (i, q) in enumerate(qs):
            progress((j, len(qs)), desc="Web check")
            k = "w" + md5(q)
            if k not in CACHE:
                h = web_hits(q)
                if h is not None: CACHE[k] = h
                time.sleep(1.5)
            pl[i] += CACHE.get(k, [])
    save_cache()
    rows, words_f = [], 0
    for i, b in enumerate(blocks):
        st = "background:rgba(255,90,90,.18);border-left:4px solid #e44;" if flag[i] else "border-left:4px solid #8884;"
        tag = ""
        if ai[i]:
            r = ai[i]["r"]
            tag += f"<small>AI score {ai[i]['b']:.3f}" + (f" · RoBERTa {r:.0%}" if r is not None else "") + "</small> "
        if pl[i]:
            st += "outline:2px solid #db0;"
            tag += "<br><small>⚠ matches: " + html.escape("; ".join(dict.fromkeys(pl[i]))) + "</small>"
        words_f += len(b.split()) if flag[i] else 0
        rows.append(f"<div style='{st}padding:8px 12px;margin:8px 0'>{html.escape(b)}<br>{tag}</div>")
    total = sum(len(b.split()) for b in blocks)
    summ = (f"**{len(blocks)} blocks, {total:,} words.** AI-flagged: {words_f/max(total,1):.0%} of words "
            f"({sum(flag)} blocks). Plagiarism matches in {sum(1 for p in pl if p)} blocks. "
            "AI scores are relative signals, not proof; re-check flagged text against his own drafts.")
    return summ, "".join(rows)

with gr.Blocks(title="Thesis Checker") as demo:
    gr.Markdown("# Thesis Checker\nAI-text detection + plagiarism check for whole papers (.docx / .pdf / .txt).")
    with gr.Row():
        thesis = gr.File(label="Thesis", type="filepath")
        refs = gr.File(label="Optional: reference papers/sources to compare against", type="filepath", file_count="multiple")
    with gr.Row():
        use_ai = gr.Checkbox(True, label="AI detection"); use_rob = gr.Checkbox(True, label="+ RoBERTa second opinion")
        size = gr.Dropdown(["0.5B", "1.5B", "3B"], value="1.5B" if torch.cuda.is_available() else "0.5B", label="Model size")
        sens = gr.Slider(0.2, 3, 1.0, step=0.1, label="Flag sensitivity (higher = flags less)")
    calib = gr.Textbox(lines=3, label="Optional: paste a few paragraphs the author definitely wrote himself (calibrates the detector)")
    with gr.Row():
        use_local = gr.Checkbox(True, label="Compare with uploaded sources"); use_web = gr.Checkbox(True, label="Web + academic check")
        nq = gr.Slider(10, 1000, 150, step=10, label="Max web queries (rate limits apply)")
    btn = gr.Button("Run check", variant="primary")
    summ, out = gr.Markdown(), gr.HTML()
    btn.click(run, [thesis, refs, use_ai, use_rob, size, use_local, use_web, nq, calib, sens], [summ, out])

if __name__ == "__main__":
    pw = os.environ.get("APP_PASS")
    demo.queue().launch(share=True, auth=("user", pw) if pw else None)
