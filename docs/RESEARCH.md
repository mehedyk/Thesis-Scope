# Research notes (as of Oct 2026)

## AI-text detectors
- **Binoculars / Fast-DetectGPT**: strong on the RAID benchmark (~96% detection at 5% false positives) but much weaker on mixed human / AI-edited / AI-written data; one third-party evaluation reports low accuracy on identifying human text. https://arxiv.org/abs/2405.07940 · https://huggingface.co/yaoandy107/greyscope-qwen3.5-4b
- **Open Pangram (EditLens)**: open checkpoints (RoBERTa-large 355M, Llama-3.2-3B) and a 60k-example dataset; three-way human / AI-edited / AI-generated framing. Licensed **CC BY-NC-SA 4.0 (non-commercial)**; authors say not to use it to enforce AI-use policies. https://www.pangram.com/blog/introducing-open-pangram
- **Greyscope (Qwen3.5-4B)**: community model fine-tuned on EditLens data, outputs a 0–1 score. https://huggingface.co/yaoandy107/greyscope-qwen3.5-4b
- **MELD**: reported strongest open-source detector on the RAID leaderboard (May 2026). Weights availability unchecked. https://arxiv.org/abs/2605.06903
- **Other languages**: detectors degrade for low-resource languages (e.g. Hindi/Tamil/Telugu benchmark). https://github.com/NLP2CT/IndicDetect
- Takeaway: use calibrated thresholds, show bands not percentages, never treat a score as proof.

## Source checking
- **infini-gram**: free API for exact n-gram counts over open corpora (RedPajama, Dolma, Pile, C4). Fixed snapshots, no recent web. https://infini-gram.readthedocs.io/en/latest/api.html
- **OpenAlex**: since Feb 2026 a free API key is recommended; $1/day free usage, full-text search costs about $0.001 per call (≈1,000 searches/day). https://developers.openalex.org/api-reference/authentication
- **Semantic Scholar snippet search** and **DuckDuckGo**: free but rate-limited and fragile from cloud IPs.
- **Crossref**: free, good for reference verification.

## Hosting
See `HOSTING.md`. Verify limits before relying on any free tier; they change often.

## Ideas not yet built
Sentence-level scoring · paraphrase detection with sentence embeddings · OpenAlex full-text lookups · World Bank/standard-definition matcher · draft-to-draft comparison · PDF/HTML report export · Greyscope/MELD as extra detectors.
