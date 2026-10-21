"""Paper/site agreement: the deployed PDF is the compiled manuscript, and shared metadata match the source."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
meta = json.loads((ROOT / "paper" / "build" / "meta.json").read_text(encoding="utf-8"))
pdf = ROOT / "site" / "dist" / "paper" / "cipher-paper.pdf"
if not pdf.exists() or hashlib.sha256(pdf.read_bytes()).hexdigest() != meta["pdf_sha256"]:
    errors.append("site PDF is missing or differs from paper/build/meta.json pdf_sha256")
body = (ROOT / "paper" / "body.tex").read_text(encoding="utf-8")
if meta["title"] not in body:
    errors.append("title in meta.json differs from body.tex")
for a in meta["authors"]:
    if a["name"] not in body or a["email"] not in body:
        errors.append(f"author {a['name']} differs between meta.json and body.tex")
status = json.loads((ROOT / "analysis" / "exports" / "status.json").read_text(encoding="utf-8"))
if status.get("version") != meta.get("version"):
    errors.append("site status version differs from paper meta version")
html = (ROOT / "paper" / "build" / "paper.html").read_text(encoding="utf-8")
gen = (ROOT / "paper" / "generated" / "corpus.tex").read_text(encoding="utf-8")
for name, val in re.findall(r"\\newcommand\{\\(N\w+)\}\{([^}]*)\}", gen):
    if "\\" + name in body and val not in html:
        errors.append(f"corpus number {name}={val} missing from paper.html")
print("\n".join(errors) or "consistency ok")
sys.exit(1 if errors else 0)
