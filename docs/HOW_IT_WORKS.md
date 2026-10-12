# How it works

**Blocks.** The paper (references removed) is cut into blocks of 150–300 words. Each block gets one rating.

**EditLens** (Open Pangram, RoBERTa-large, 512 tokens): scores 0–1 for how much text looks AI-written or AI-edited. v2 averages the model's output into one number (assumption to verify; see `TESTING.md`). Thresholds: High ≥ 0.60, Medium ≥ 0.35. With a known-human sample, High is raised to at least the highest human score.

**Binoculars:** two similar models (Qwen2.5 base + instruct). Score = perplexity / cross-perplexity. Low = predictable to LLMs = machine-like. A block is flagged when its z-score is below −sensitivity relative to the baseline (known-human sample if given, otherwise the paper itself).

**Combined rating.** EditLens high = 2 points, medium = 1, Binoculars flag = 1. 3+ points (or 2 when only one detector is on) = **High**; 1+ = **Medium**; else **Low**. Formulaic text gets a caution note.

**Plagiarism.** (a) 8-word overlap with uploaded sources; (b) for sampled distinctive sentences, a 12-word phrase is looked up exactly in infini-gram (RedPajama), DuckDuckGo and Semantic Scholar snippets, and only counted if the returned text actually contains the phrase (fuzzy ≥ 92). Lookup failures are counted and reported.

**References.** Each reference line is matched to a Crossref title (partial match ≥ 80). “Not matched” may be a book or local report; fabricated citations also appear here.

**Cache.** `cache.json` stores scores and lookups by text hash, so reruns skip unchanged blocks.
