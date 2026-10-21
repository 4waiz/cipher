/*
 * Shared helpers for CIPHER pages. Classic script; exposes window.Cipher.
 * All data-derived strings are inserted with textContent, never as HTML.
 */
(function () {
  "use strict";

  var LABELS = [
    "Unresolved conflict",
    "Valid override",
    "Disjoint applicability",
    "Compatible",
    "Insufficient evidence"
  ];

  var GITHUB_REPO_URL = "https://github.com/4waiz/cipher";

  /** Create an element. attrs: plain attributes plus "text", "class", "html" is intentionally unsupported. */
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === null || value === undefined || value === false) return;
        if (key === "text") node.textContent = String(value);
        else if (key === "class") node.className = value;
        else if (key.indexOf("on") === 0 && typeof value === "function") node.addEventListener(key.slice(2), value);
        else node.setAttribute(key, value === true ? "" : String(value));
      });
    }
    appendAll(node, children);
    return node;
  }

  function appendAll(node, children) {
    if (children === null || children === undefined) return node;
    if (!Array.isArray(children)) children = [children];
    children.forEach(function (child) {
      if (child === null || child === undefined || child === false) return;
      if (Array.isArray(child)) appendAll(node, child);
      else if (typeof child === "string" || typeof child === "number") node.appendChild(document.createTextNode(String(child)));
      else node.appendChild(child);
    });
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  function isObject(x) {
    return x !== null && typeof x === "object" && !Array.isArray(x);
  }

  /**
   * Load one generated data file. Prefers the inlined copy (data/<name>.js sets
   * window.CIPHER_DATA[name]) so pages work from file://, then falls back to fetch.
   * Resolves to { ok: true, data } or { ok: false, error }.
   */
  function loadData(name, base) {
    var inline = window.CIPHER_DATA && Object.prototype.hasOwnProperty.call(window.CIPHER_DATA, name)
      ? window.CIPHER_DATA[name] : undefined;
    if (inline !== undefined) return Promise.resolve({ ok: true, data: inline, source: "inline" });
    if (typeof fetch !== "function") return Promise.resolve({ ok: false, error: new Error("fetch is not available") });
    var url = (base || "") + "data/" + name + ".json";
    return fetch(url, { cache: "no-cache" })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status + " for " + url);
        return res.json();
      })
      .then(function (data) { return { ok: true, data: data, source: "fetch" }; })
      .catch(function (error) { return { ok: false, error: error, url: url }; });
  }

  /** A plain error block explaining why data could not be read. */
  function loadErrorMessage(fileLabel, result) {
    var fromDisk = location.protocol === "file:";
    var box = el("div", { class: "message is-error", role: "alert" }, [
      el("h2", { text: "Could not read " + fileLabel }),
      el("p", { text: fromDisk
        ? "This page was opened directly from disk and the inlined data file was not found, so the browser blocked reading the JSON."
        : "The data file could not be loaded." }),
      el("p", null, [
        "Rebuild the site with ",
        el("code", { class: "code-inline", text: "python site/build.py" }),
        " and serve the output folder, for example ",
        el("code", { class: "code-inline", text: "python -m http.server 8000 --directory site/dist" }),
        ", then open http://localhost:8000/."
      ])
    ]);
    if (result && result.error) {
      box.appendChild(el("p", { class: "note", text: "Technical detail: " + String(result.error.message || result.error) }));
    }
    return box;
  }

  function shortCommit(commit) {
    return typeof commit === "string" ? commit.slice(0, 7) : "";
  }

  var REPO_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
  var COMMIT_RE = /^[0-9a-f]{7,40}$/i;

  function encodePath(path) {
    return String(path).split("/").map(encodeURIComponent).join("/");
  }

  /** Pinned GitHub link for a source span, or null if the inputs are not well formed. */
  function blobUrl(repo, commit, path, start, end) {
    if (!REPO_RE.test(String(repo || "")) || !COMMIT_RE.test(String(commit || "")) || !path) return null;
    var url = "https://github.com/" + repo + "/blob/" + commit + "/" + encodePath(path);
    if (Number.isInteger(start) && start > 0) {
      url += "#L" + start;
      if (Number.isInteger(end) && end > start) url += "-L" + end;
    }
    return url;
  }

  function treeUrl(repo, commit) {
    if (!REPO_RE.test(String(repo || "")) || !COMMIT_RE.test(String(commit || ""))) return null;
    return "https://github.com/" + repo + "/tree/" + commit;
  }

  /** Fill footer build line from data/build.js when present. */
  function fillBuildInfo() {
    var slot = document.getElementById("build-info");
    if (!slot) return;
    var info = window.CIPHER_DATA && window.CIPHER_DATA.build;
    if (!isObject(info) || !info.site_built_utc) return;
    slot.textContent = "Site built " + String(info.site_built_utc).replace("T", " ").replace(/\.\d+/, "").replace("Z", " UTC") + ".";
  }

  document.addEventListener("DOMContentLoaded", fillBuildInfo);

  window.Cipher = {
    LABELS: LABELS,
    GITHUB_REPO_URL: GITHUB_REPO_URL,
    el: el,
    clear: clear,
    appendAll: appendAll,
    isObject: isObject,
    loadData: loadData,
    loadErrorMessage: loadErrorMessage,
    shortCommit: shortCommit,
    blobUrl: blobUrl,
    treeUrl: treeUrl
  };
})();
