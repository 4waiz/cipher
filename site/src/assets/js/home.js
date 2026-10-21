/* Home page: status line and availability of generated outputs. */
(function () {
  "use strict";
  var C = window.Cipher;
  if (!C) return;
  var el = C.el;

  var DEFAULT_STATUS = "pilot study in progress — results not yet available";

  function setStatus(data, loadFailed) {
    var text = document.getElementById("status-text");
    var meta = document.getElementById("status-meta");
    if (!text || !meta) return;
    C.clear(meta);

    var usable = C.isObject(data) && data.available !== false && typeof data.status_label === "string" && data.status_label.trim();
    if (!usable) {
      text.textContent = DEFAULT_STATUS;
      meta.textContent = loadFailed
        ? "Could not read data/status.json; showing the default status. Serve the built site over HTTP if you opened it from disk."
        : "No status export yet (analysis/exports/status.json was not present at build time).";
      return;
    }

    text.textContent = data.status_label.trim();
    var parts = [];
    if (data.version) parts.push("Version " + String(data.version));
    if (data.date) parts.push(String(data.date));
    meta.appendChild(document.createTextNode(parts.join(" · ")));
    if (typeof data.git_commit === "string" && /^[0-9a-f]{7,40}$/i.test(data.git_commit)) {
      if (parts.length) meta.appendChild(document.createTextNode(" · "));
      meta.appendChild(document.createTextNode("commit "));
      meta.appendChild(el("a", {
        class: "mono",
        href: C.GITHUB_REPO_URL + "/commit/" + data.git_commit,
        text: C.shortCommit(data.git_commit)
      }));
    }
  }

  function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }

  function setAvailability(build, loadFailed) {
    var r = document.getElementById("avail-results");
    var c = document.getElementById("avail-replay");
    var p = document.getElementById("avail-paper");
    var outputs = C.isObject(build) && C.isObject(build.outputs) ? build.outputs : null;

    if (!outputs) {
      var msg = loadFailed ? "Build information could not be read." : "Build information not available.";
      [r, c, p].forEach(function (n) { if (n) n.textContent = msg; });
      return;
    }

    var res = outputs.results || {};
    if (r) {
      r.textContent = res.present && res.available === true
        ? "Available: " + plural(res.tables || 0, "table") + ", " + plural(res.figures || 0, "figure") + "."
        : "Not yet available.";
    }
    var rep = outputs.replay || {};
    if (c) {
      c.textContent = rep.present && rep.available === true
        ? "Available: " + plural(rep.cases || 0, "recorded case") + "."
        : "Not yet available.";
    }
    var paper = outputs.paper || {};
    if (p) {
      if (paper.html) p.textContent = "Web version built" + (paper.pdf ? "; compiled PDF available." : "; PDF not yet compiled.");
      else if (paper.pdf) p.textContent = "Compiled PDF available; web version not yet built.";
      else p.textContent = "Manuscript not yet built.";
    }
  }

  C.loadData("status", "").then(function (result) {
    setStatus(result.ok ? result.data : null, !result.ok);
  });
  C.loadData("build", "").then(function (result) {
    setAvailability(result.ok ? result.data : null, !result.ok);
  });
})();
