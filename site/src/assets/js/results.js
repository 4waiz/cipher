/* Results page: generic rendering of data/results.json (see docs/site_contract.md). */
(function () {
  "use strict";
  var C = window.Cipher;
  if (!C) return;
  var el = C.el;
  var root = document.getElementById("results-root");
  if (!root) return;

  var UNDEFINED_TITLE = "undefined: empty denominator";

  function unavailable(reason) {
    return el("div", { class: "message" }, [
      el("h2", { text: "Results are not yet available" }),
      el("p", null, reason
        ? ["Reason: ", el("span", { class: "reason", text: String(reason) })]
        : "The export did not record a reason."),
      el("p", { class: "note", text: "No numbers are shown until the analysis pipeline exports them." })
    ]);
  }

  function contractError(problem) {
    return el("div", { class: "message is-error", role: "alert" }, [
      el("h2", { text: "results.json does not match the site contract" }),
      el("p", { text: problem }),
      el("p", { class: "note", text: "Nothing is shown rather than a partial or misread table. See docs/site_contract.md." })
    ]);
  }

  function cellNode(tag, value, isNumericColumn) {
    if (value === null || value === undefined) {
      return el(tag, { class: isNumericColumn ? "num" : null }, el("span", {
        class: "undef",
        title: UNDEFINED_TITLE,
        "aria-label": UNDEFINED_TITLE,
        text: "–"
      }));
    }
    var isNum = typeof value === "number";
    return el(tag, { class: isNum || isNumericColumn ? "num" : null, text: String(value) });
  }

  function renderTable(table, index) {
    if (!C.isObject(table) || !Array.isArray(table.columns) || !Array.isArray(table.rows)) {
      return contractError("Table " + (index + 1) + " is missing its columns or rows array.");
    }
    var cols = table.columns;
    var numericCol = cols.map(function (_, ci) {
      var seen = false;
      for (var ri = 0; ri < table.rows.length; ri++) {
        var v = Array.isArray(table.rows[ri]) ? table.rows[ri][ci] : undefined;
        if (v === null || v === undefined) continue;
        if (typeof v !== "number") return false;
        seen = true;
      }
      return seen;
    });

    var baseId = "table-" + (typeof table.id === "string" && /^[\w-]+$/.test(table.id) ? table.id : String(index + 1));
    var titleId = baseId + "-title";
    var captionId = baseId + "-caption";

    var thead = el("thead", null, el("tr", null, cols.map(function (c, ci) {
      return el("th", { scope: "col", class: numericCol[ci] ? "num" : null, text: String(c) });
    })));
    var tbody = el("tbody", null, table.rows.map(function (row) {
      var cells = Array.isArray(row) ? row : [];
      return el("tr", null, cols.map(function (_, ci) {
        // First column acts as the row header.
        return ci === 0
          ? (function () { var th = cellNode("th", cells[ci], numericCol[ci]); th.setAttribute("scope", "row"); return th; })()
          : cellNode("td", cells[ci], numericCol[ci]);
      }));
    }));

    var tableEl = el("table", { class: "data-table", "aria-labelledby": titleId, "aria-describedby": table.caption ? captionId : null }, [thead, tbody]);
    var scroller = el("div", { class: "table-scroll", role: "region", tabindex: "0", "aria-labelledby": titleId }, tableEl);

    return el("section", { class: "table-block", id: baseId, "aria-labelledby": titleId }, [
      el("h2", { id: titleId, text: table.title ? String(table.title) : "Table " + (index + 1) }),
      table.caption ? el("p", { class: "caption", id: captionId, text: String(table.caption) }) : null,
      scroller,
      table.rows.length === 0 ? el("p", { class: "table-notes", text: "The table has no rows." }) : null,
      table.notes ? el("p", { class: "table-notes", text: String(table.notes) }) : null
    ]);
  }

  function figureSrc(path) {
    // Figures are copied next to the paper by the build (paper/figures/<name>.svg).
    var p = String(path || "");
    if (!/^figures\/[\w.-]+\.(svg|png)$/i.test(p)) return null;
    return "../paper/" + p;
  }

  function renderFigure(fig, index) {
    if (!C.isObject(fig)) return contractError("Figure " + (index + 1) + " is not an object.");
    var src = figureSrc(fig.path);
    var titleText = fig.title ? String(fig.title) : "Figure " + (index + 1);
    var frame = el("div", { class: "figure-frame" });
    if (src) {
      var img = el("img", { src: src, alt: titleText + (fig.caption ? ". " + fig.caption : ""), loading: "lazy" });
      img.addEventListener("error", function () {
        C.clear(frame);
        frame.appendChild(el("p", { class: "note", text: "Figure file not found in this build: " + String(fig.path) }));
      });
      frame.appendChild(img);
    } else {
      frame.appendChild(el("p", { class: "note", text: "Figure path does not match the contract (figures/<name>.svg): " + String(fig.path) }));
    }
    return el("section", { class: "figure-block", "aria-label": titleText }, el("figure", null, [
      el("h2", { text: titleText }),
      frame,
      fig.caption ? el("figcaption", { text: String(fig.caption) }) : null
    ]));
  }

  function render(data) {
    C.clear(root);
    if (!C.isObject(data)) {
      root.appendChild(contractError("The file is not a JSON object."));
      return;
    }
    if (data.available !== true) {
      root.appendChild(unavailable(data.reason));
      return;
    }
    var tables = Array.isArray(data.tables) ? data.tables : null;
    var figures = Array.isArray(data.figures) ? data.figures : [];
    if (!tables) {
      root.appendChild(contractError("\"available\" is true but \"tables\" is not an array."));
      return;
    }

    if (tables.length) {
      tables.forEach(function (t, i) { root.appendChild(renderTable(t, i)); });
    } else {
      root.appendChild(el("p", { class: "note", text: "The export contains no tables." }));
    }
    figures.forEach(function (f, i) { root.appendChild(renderFigure(f, i)); });

    if (Array.isArray(data.limitations) && data.limitations.length) {
      root.appendChild(el("section", { class: "table-block", "aria-labelledby": "limitations-title" }, [
        el("h2", { id: "limitations-title", text: "Limitations" }),
        el("ul", { class: "prose" }, data.limitations.map(function (l) { return el("li", { text: String(l) }); }))
      ]));
    }
  }

  C.loadData("results", "../").then(function (result) {
    if (!result.ok) {
      C.clear(root);
      root.appendChild(C.loadErrorMessage("data/results.json", result));
      return;
    }
    render(result.data);
  });
})();
