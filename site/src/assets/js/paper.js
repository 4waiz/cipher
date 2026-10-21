/* Paper page: Cite button, section self-links, table-of-contents highlight. */
(function () {
  "use strict";

  // ----- Cite: copy BibTeX from meta.json (rendered into #bibtex at build time) -----
  var citeBtn = document.getElementById("cite-btn");
  var bib = document.getElementById("bibtex");
  var status = document.getElementById("cite-status");

  function say(msg) { if (status) status.textContent = msg; }

  function selectBib() {
    if (!bib) return;
    bib.focus();
    var range = document.createRange();
    range.selectNodeContents(bib);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  function legacyCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "-1000px";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  if (citeBtn && bib) {
    var label = citeBtn.textContent;
    citeBtn.addEventListener("click", function () {
      var text = bib.textContent;
      var done = function () {
        say("BibTeX copied to the clipboard.");
        citeBtn.textContent = "Copied";
        setTimeout(function () { citeBtn.textContent = label; }, 2000);
      };
      var fail = function () {
        if (legacyCopy(text)) { done(); return; }
        say("Could not copy automatically. The BibTeX entry is selected at the end of the page; press Ctrl+C or Cmd+C.");
        selectBib();
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, fail);
      } else {
        fail();
      }
    });
  }

  // ----- Self-links on section headings -----
  var sections = Array.prototype.slice.call(document.querySelectorAll(".paper-body section[id]"));
  sections.forEach(function (sec) {
    var h = sec.querySelector("h1, h2, h3, h4");
    if (!h || h.closest("section") !== sec || h.querySelector(".heading-anchor")) return;
    var a = document.createElement("a");
    a.className = "heading-anchor";
    a.href = "#" + sec.id;
    a.textContent = "#";
    a.setAttribute("aria-label", "Link to section: " + h.textContent.trim());
    h.appendChild(a);
  });

  // ----- Highlight the current section in the table of contents -----
  var tocLinks = {};
  Array.prototype.forEach.call(document.querySelectorAll(".toc a[href^='#']"), function (a) {
    tocLinks[decodeURIComponent(a.getAttribute("href").slice(1))] = a;
  });
  var tracked = sections.filter(function (s) { return tocLinks[s.id]; });
  if (!tracked.length) return;

  var current = null;
  var pending = false;
  function updateCurrent() {
    pending = false;
    // The current section is the last one (in document order, so nested ones win) whose top has scrolled past the bar.
    var next = tracked[0].id;
    for (var i = 0; i < tracked.length; i++) {
      if (tracked[i].getBoundingClientRect().top <= 110) next = tracked[i].id;
    }
    if (next === current) return;
    current = next;
    Object.keys(tocLinks).forEach(function (id) {
      if (id === current) tocLinks[id].setAttribute("aria-current", "true");
      else tocLinks[id].removeAttribute("aria-current");
    });
  }
  window.addEventListener("scroll", function () {
    if (!pending) { pending = true; window.requestAnimationFrame(updateCurrent); }
  }, { passive: true });
  updateCurrent();
})();
