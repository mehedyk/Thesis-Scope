# Testing & calibration protocol

1. Run the whole paper once; confirm it completes and the summary reports how many lookups succeeded.
2. **EditLens direction check:** run (a) a paragraph you know a person wrote, (b) a ChatGPT paragraph on the same topic, (c) the human paragraph polished by ChatGPT. Expect a < c < b. If not, adjust or invert the score mapping in `Detector.edit`.
3. **Binoculars check:** the AI paragraph should have a clearly lower score than the human one.
4. Paste the human paragraphs into **Known-human sample** and rerun; High threshold should rise to cover them.
5. Plagiarism: paste a sentence you know exists online; it should appear under overlaps. Check the “lookups failed” count.
6. If the checks pass, record thresholds in `docs/HISTORY.md`.
