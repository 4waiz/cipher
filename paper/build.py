"""Build the manuscript: named and anonymous PDFs (Tectonic + IEEEtran), an HTML fragment for the site (Pandoc from
the same body.tex), metadata, and page renders for visual inspection.

  python paper/build.py [--tectonic PATH]

Outputs in paper/build/: cipher-paper.pdf (named), cipher-paper-anonymous.pdf, paper.html, meta.json, pages/*.png
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BUILD = HERE / "build"
TITLE = "CIPHER: Contextual Instruction Precedence and Hierarchy Evaluation for Repositories"
AUTHORS = [{"name": "Awaiz Ahmed", "affiliation": "Al Ain University, United Arab Emirates",
            "email": "202310183@aau.ac.ae"},
           {"name": "Mohammad Umar", "affiliation": "Al Ain University, United Arab Emirates",
            "email": "202240077@aau.ac.ae"},
           {"name": "Huda Mueen", "affiliation": "Al Ain University, United Arab Emirates",
            "email": "Hudamueen2407@gmail.com"}]


def find_tectonic(arg: str | None) -> str:
    for c in [arg, shutil.which("tectonic"), str(ROOT.parent / ".tools" / "tectonic" / "tectonic.exe")]:
        if c and Path(c).exists():
            return c
    sys.exit("Tectonic not found: pass --tectonic PATH (https://tectonic-typesetting.github.io)")


def pdf(tectonic: str, stem: str, out_name: str) -> Path:
    subprocess.run([tectonic, "--keep-logs", "--outdir", str(BUILD), f"{stem}.tex"], cwd=HERE, check=True)
    out = BUILD / out_name
    shutil.move(BUILD / f"{stem}.pdf", out)
    return out


def html_fragment() -> str:
    """Pandoc HTML from body.tex: named branch of \\ifanon, generated macros inlined, figures as SVG."""
    import pypandoc
    body = (HERE / "body.tex").read_text(encoding="utf-8")
    have_results = "\\resultstrue" in (HERE / "generated" / "results.tex").read_text(encoding="utf-8")
    body = body.replace("\\newif\\ifresults", "")  # before branch selection, or the pattern below would match it
    body = re.sub(r"\\ifresults(.*?)\\else(.*?)\\fi", lambda m: m.group(1 if have_results else 2), body, flags=re.S)
    for inc in re.findall(r"\\input\{([^}]+)\}", body):
        f = HERE / (inc if inc.endswith(".tex") else inc + ".tex")
        body = body.replace(f"\\input{{{inc}}}", f.read_text(encoding="utf-8"))
    body = body.replace("\\resultstrue", "").replace("\\resultsfalse", "").replace("build/figures/", "figures/")
    body = re.sub(r"\\ifanon.*?\\else(.*?)\\fi", r"\1", body, flags=re.S)
    body = re.sub(r"\\title\{.*?\}\n", "", body)
    body = re.sub(r"\\author\{.*?\n\}?\n\n", "", body, flags=re.S)
    body = body.replace("\\maketitle", "")
    body = body.replace("\\begin{abstract}", "\\section*{Abstract}\\label{abstract}").replace("\\end{abstract}", "")
    body = re.sub(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", r"\\textbf{Keywords:} \1", body, flags=re.S)
    body = re.sub(r"\\bibliographystyle\{[^}]*\}\s*\\bibliography\{[^}]*\}", r"\\section*{References}\\label{references}",
                  body)
    body = re.sub(r"(\\includegraphics(?:\[[^]]*\])?\{[^}]*?)\.pdf\}", r"\1.svg}", body)
    tex = "\\documentclass{article}\n\\begin{document}\n" + body + "\n\\end{document}\n"
    return pypandoc.convert_text(tex, "html5", format="latex", extra_args=[
        "--citeproc", f"--bibliography={HERE / 'refs.bib'}", f"--csl={HERE / 'ieee.csl'}", "--section-divs",
        "--mathml", "--metadata=link-citations:true", "--resource-path", str(HERE)])


def render_pages(p: Path, tag: str) -> int:
    import fitz
    d = fitz.open(p)
    out = BUILD / "pages"
    out.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(d):
        page.get_pixmap(dpi=110).save(out / f"{tag}-p{i + 1}.png")
    return d.page_count


def abstract_text() -> str:
    """Plain-text abstract with generated macros expanded (empty while results are pending)."""
    import pypandoc
    res = (HERE / "generated" / "results.tex").read_text(encoding="utf-8")
    src = HERE / "prose" / "abstract.tex"
    if "\\resultstrue" not in res or not src.exists():
        return ""
    macros = (HERE / "generated" / "corpus.tex").read_text(encoding="utf-8") + res.replace("\\resultstrue", "")
    return pypandoc.convert_text(macros + "\n" + src.read_text(encoding="utf-8"), "plain", format="latex",
                                 extra_args=["--wrap=none"]).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tectonic")
    args = ap.parse_args()
    tec = find_tectonic(args.tectonic)
    BUILD.mkdir(exist_ok=True)
    named = pdf(tec, "cipher-named", "cipher-paper.pdf")
    anon = pdf(tec, "cipher-anon", "cipher-paper-anonymous.pdf")
    (BUILD / "paper.html").write_text(html_fragment(), encoding="utf-8", newline="\n")
    status = json.loads((ROOT / "analysis" / "exports" / "status.json").read_text(encoding="utf-8")) \
        if (ROOT / "analysis" / "exports" / "status.json").exists() else {}
    authors = "Ahmed, Awaiz and Umar, Mohammad and Mueen, Huda"
    meta = {"title": TITLE, "authors": AUTHORS, "abstract": abstract_text(),
            "version": status.get("version", "draft"), "date": status.get("date", date.today().isoformat()),
            "status": status.get("status_label", ""),
            "citation_bibtex": "@misc{ahmed2026cipher,\n  author = {" + authors + "},\n  title = {{" + TITLE +
                               "}},\n  year = {2026},\n  note = {Manuscript submitted to TEXTUAL 2027 (SANER 2027 "
                               "workshop); under review},\n  url = {https://github.com/4waiz/cipher}\n}",
            "pdf_sha256": hashlib.sha256(named.read_bytes()).hexdigest(),
            "anonymous_pdf_sha256": hashlib.sha256(anon.read_bytes()).hexdigest(),
            "pages": {"named": render_pages(named, "named"), "anonymous": render_pages(anon, "anon")}}
    (BUILD / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({k: meta[k] for k in ("version", "pages", "pdf_sha256")}, indent=1))


if __name__ == "__main__":
    main()
