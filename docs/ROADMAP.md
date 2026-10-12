# Roadmap

- [x] v1 working in Colab on a real 7k-word paper
- [x] v2 code: EditLens, infini-gram, Crossref, writing checks, explainable UI, animated assets
- [ ] **Phase 0 – Verify & calibrate (do first):** run v2 once; check EditLens direction on known human/AI text; build a small test set (human student papers, ChatGPT text on same topic, AI-polished versions); choose thresholds at ~5% false positives
- [ ] **Phase 1 – Better detection:** sentence-level scoring, Greyscope/MELD as optional detectors, per-section verdicts, confidence bands
- [ ] **Phase 2 – Better plagiarism:** OpenAlex full-text lookups, embedding-based paraphrase detection, definition matcher, “quoted and cited” awareness
- [ ] **Phase 3 – Quality checks:** duplicate section numbers, figure/table reference consistency, inconsistent sample sizes
- [ ] **Phase 4 – UX:** exportable PDF/HTML report, side-by-side source view, draft-to-draft comparison
- [ ] **Phase 5 – Hosting:** password-protected permanent deployment (see HOSTING.md)
