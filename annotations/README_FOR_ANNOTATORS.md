# CIPHER annotation: instructions for annotators

Annotators: A1 = Awaiz Ahmed, A2 = Mohammad Umar. Adjudicator: Huda Mueen (does not annotate independently).

## What to do

1. Open your own file in Chrome, Edge or Firefox by double-clicking it. No internet or installation is needed.
   - A1: `CIPHER_calibration_A1.html`, then `CIPHER_evaluation_A1.html`
   - A2: `CIPHER_calibration_A2.html`, then `CIPHER_evaluation_A2.html`
2. Click **Handbook** and read it once (5 minutes). The same text is in `docs/annotation_handbook.md`.
3. **Calibration (about 30-40 minutes, 20 items).** Items P1-P6 are authored practice items: after you save, the
   handbook answer appears. The other 14 are real repository cases without answers.
   Click **Export JSON** when finished and send the file to Awaiz.
4. After both calibration files are in, the three of you may discuss calibration disagreements. Do not change the
   handbook afterwards without telling Awaiz (changes are logged).
5. **Evaluation (about 1.5-2.5 hours, 54 items).** Work alone. Do not discuss evaluation cases with anyone, do not look at
   the other annotator's file, and do not look up the repositories. Progress saves automatically in your browser; still
   click **Export JSON** at the end (and whenever you take a break). Send the exported JSON file to Awaiz.
6. Every item needs a label and a short reason. The other fields help the analysis; fill them when you can.

## Rules that keep the study valid

- Your judgments must be your own. Do not ask an AI system for answers, and do not copy answers between annotators.
- Some cases are researcher-constructed variations of real files. Label each case exactly as it is shown.
- If decisive context seems missing, tick the missing-context box and still choose your best label.
- Do not edit an exported file by hand.

## Where the exported files go

Awaiz saves each file unchanged as:
`annotations/submissions/<packet>_<A1|A2>.json` (for example `annotations/submissions/evaluation_A2.json`).
