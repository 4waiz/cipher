/*
 * Recorded cases (replay). Renders data/replay.json; nothing here calls a model.
 * Case text comes from third-party repositories: it is always inserted as text.
 */
(function () {
  "use strict";
  var C = window.Cipher;
  if (!C) return;
  var el = C.el;
  var root = document.getElementById("cases-root");
  if (!root) return;

  var LABELS = C.LABELS;
  var STRATA = ["original", "context_variant", "order_control"];
  var STRATUM_NAMES = { original: "Original", context_variant: "Context variant", order_control: "Order control" };
  var METHODS = ["B0", "B1", "B2"];
  var METHOD_NAMES = { B0: "Keyword heuristic", B1: "Direct contextual LLM", B2: "Structured pipeline" };
  var PENDING = "__pending";

  var state = { cases: [], byId: {}, stratum: "all", label: "all", currentId: null };

  function str(x) { return x === null || x === undefined ? "" : String(x); }
  function stratumName(s) { return STRATUM_NAMES[s] || str(s) || "unknown"; }
  function refLabel(c) { return C.isObject(c.reference) && typeof c.reference.label === "string" && c.reference.label ? c.reference.label : null; }

  // ----- comparison with the human reference ---------------------------------

  /** Returns { state: "match"|"mismatch"|"none", text } for one method's saved output. */
  function compare(method, pred, ref) {
    if (!pred || ref === null) return { state: "none" };
    if (method === "B0") {
      if (typeof pred.conflict_flag !== "boolean") return { state: "none" };
      var expected = ref === "Unresolved conflict";
      return pred.conflict_flag === expected ? { state: "match" } : { state: "mismatch" };
    }
    if (pred.error || typeof pred.label !== "string" || !pred.label) return { state: "none" };
    return pred.label === ref ? { state: "match" } : { state: "mismatch" };
  }

  function mismatches(c) {
    var ref = refLabel(c);
    var preds = C.isObject(c.predictions) ? c.predictions : {};
    return METHODS.filter(function (m) { return compare(m, preds[m], ref).state === "mismatch"; });
  }

  // ----- messages -------------------------------------------------------------

  function unavailable(reason) {
    return el("div", { class: "message" }, [
      el("h2", { text: "Recorded cases are not yet available" }),
      el("p", null, reason
        ? ["Reason: ", el("span", { class: "reason", text: str(reason) })]
        : "The export did not record a reason."),
      el("p", { class: "note", text: "No cases are shown until saved runs are exported." })
    ]);
  }

  function contractError(problem) {
    return el("div", { class: "message is-error", role: "alert" }, [
      el("h2", { text: "replay.json does not match the site contract" }),
      el("p", { text: problem }),
      el("p", { class: "note", text: "See docs/site_contract.md." })
    ]);
  }

  // ----- list + filters -------------------------------------------------------

  var listEl, countEl, detailEl, stratumSel, labelSel;

  function filtered() {
    return state.cases.filter(function (c) {
      if (state.stratum !== "all" && c.stratum !== state.stratum) return false;
      if (state.label !== "all") {
        var r = refLabel(c);
        if (state.label === PENDING ? r !== null : r !== state.label) return false;
      }
      return true;
    });
  }

  function option(value, text, selected) {
    var o = el("option", { value: value, text: text });
    if (selected) o.selected = true;
    return o;
  }

  function buildFilters() {
    var strata = STRATA.slice();
    state.cases.forEach(function (c) { if (c.stratum && strata.indexOf(c.stratum) === -1) strata.push(c.stratum); });
    var countBy = function (fn) { return state.cases.filter(fn).length; };

    stratumSel = el("select", { id: "f-stratum" }, [option("all", "All strata (" + state.cases.length + ")", true)].concat(
      strata.map(function (s) { return option(s, stratumName(s) + " (" + countBy(function (c) { return c.stratum === s; }) + ")"); })
    ));
    labelSel = el("select", { id: "f-label" }, [option("all", "All reference labels (" + state.cases.length + ")", true)].concat(
      LABELS.map(function (l) { return option(l, l + " (" + countBy(function (c) { return refLabel(c) === l; }) + ")"); }),
      [option(PENDING, "No reference label (" + countBy(function (c) { return refLabel(c) === null; }) + ")")]
    ));
    stratumSel.addEventListener("change", function () { state.stratum = stratumSel.value; renderList(); });
    labelSel.addEventListener("change", function () { state.label = labelSel.value; renderList(); });

    return el("div", { class: "filters", role: "group", "aria-label": "Filter cases" }, [
      el("div", { class: "field" }, [el("label", { for: "f-stratum", text: "Stratum" }), stratumSel]),
      el("div", { class: "field" }, [el("label", { for: "f-label", text: "Reference label" }), labelSel])
    ]);
  }

  function caseHref(id) { return "#case=" + encodeURIComponent(id); }

  function renderList() {
    var items = filtered();
    countEl.textContent = "Showing " + items.length + " of " + state.cases.length + " cases.";
    C.clear(listEl);
    if (!items.length) {
      listEl.appendChild(el("li", { class: "note", text: "No cases match these filters." }));
      return;
    }
    items.forEach(function (c) {
      var ref = refLabel(c);
      var diff = mismatches(c);
      listEl.appendChild(el("li", null, el("a", {
        class: "case-link",
        href: caseHref(c.case_id),
        "aria-current": c.case_id === state.currentId ? "true" : null
      }, [
        el("span", { class: "cid", text: c.case_id }),
        el("span", { class: "ctarget", text: str(c.target_path) }),
        el("span", { class: "crow" }, [
          el("span", { class: "chip", text: stratumName(c.stratum) }),
          el("span", { class: "badge badge-ref badge-sm" + (ref ? "" : " is-pending"), text: ref ? "Ref: " + ref : "Ref: none" }),
          ref && diff.length ? el("span", { class: "cmp is-mismatch", text: diff.join(", ") + " differ" }) : null
        ])
      ])));
    });
  }

  // ----- detail ---------------------------------------------------------------

  function kvRow(label, value) {
    return [el("dt", { text: label }), el("dd", null, value)];
  }

  function spanPanel(name, span, c) {
    if (!C.isObject(span)) {
      return el("section", { class: "evidence", "aria-label": name + " source span" }, [
        el("div", { class: "evidence-head" }, el("span", { class: "who", text: name + ": span missing in export" }))
      ]);
    }
    var start = Number.isInteger(span.start_line) ? span.start_line : null;
    var end = Number.isInteger(span.end_line) ? span.end_line : start;
    var where = str(span.path) + (start ? ":" + start + (end && end !== start ? "–" + end : "") : "");
    var url = C.blobUrl(c.repo, c.commit, span.path, start, end);
    var lines = str(span.text).replace(/\r\n?/g, "\n").split("\n");
    var pre = el("pre", { class: "code wrap", tabindex: "0", "aria-label": name + " text, " + where });
    lines.forEach(function (t, i) {
      pre.appendChild(el("span", { class: "line" }, [
        el("span", { class: "ln", "aria-hidden": "true", text: start ? String(start + i) : "" }),
        el("span", { class: "tx", text: t || " " })
      ]));
    });
    return el("section", { class: "evidence", "aria-label": name + " source span" }, [
      el("div", { class: "evidence-head" }, [
        el("span", null, [el("span", { class: "who", text: name + "  " }), el("span", { class: "where", text: where })]),
        url ? el("a", { href: url, class: "small ext", text: "View at pinned commit" }) : el("span", { class: "meta", text: "No pinned link (repo or commit missing)" })
      ]),
      span.heading ? el("div", { class: "evidence-sub" }, ["Under heading ", el("span", { class: "where", text: str(span.heading) })]) : null,
      pre
    ]);
  }

  function referenceBlock(c) {
    var ref = C.isObject(c.reference) ? c.reference : {};
    var label = refLabel(c);
    var a1 = typeof ref.annotator_1 === "string" ? ref.annotator_1 : null;
    var a2 = typeof ref.annotator_2 === "string" ? ref.annotator_2 : null;
    var disagreed = a1 && a2 && a1 !== a2;

    var body = el("div", { class: "jbody" });
    if (a1 || a2) {
      body.appendChild(el("p", null, ["Annotator 1: ", el("strong", { text: a1 || "not recorded" }), " · Annotator 2: ", el("strong", { text: a2 || "not recorded" })]));
    }
    if (disagreed) {
      body.appendChild(el("div", { class: "disagree" }, [
        el("strong", { text: "Annotators disagreed. " }),
        label ? (ref.status === "adjudicated" ? "Adjudicated as " + label + "." : "Reference recorded as " + label + ".") : "No adjudicated label yet.",
        ref.adjudication_reason ? el("p", { class: "small", text: "Adjudication note: " + str(ref.adjudication_reason) }) : null
      ]));
    } else if (ref.adjudication_reason) {
      body.appendChild(el("p", { class: "small", text: "Adjudication note: " + str(ref.adjudication_reason) }));
    }

    return el("div", { class: "judgement reference" }, [
      el("div", { class: "jhead" }, [
        el("span", { class: "badge badge-ref" + (label ? "" : " is-pending"), text: label || "None" }),
        el("span", { class: "chip", text: "Reference" + (ref.status ? " · " + str(ref.status) : "") })
      ]),
      body.childNodes.length ? body : null
    ]);
  }

  function predictionBlock(method, pred, ref) {
    var cmp = compare(method, pred, ref);
    var badgeText;
    var badgeClass = "badge badge-pred";
    var body = el("div", { class: "jbody" });

    if (!pred) {
      badgeText = "No saved output";
      badgeClass += " is-missing";
    } else if (method === "B0") {
      badgeText = typeof pred.conflict_flag === "boolean" ? (pred.conflict_flag ? "Conflict flagged" : "No conflict flagged") : "Flag missing";
      if (typeof pred.conflict_flag !== "boolean") badgeClass += " is-missing";
      body.appendChild(el("p", { class: "note small", text: "B0 is binary. It is compared with whether the reference label is Unresolved conflict." }));
    } else if (pred.error) {
      badgeText = "Run error";
      badgeClass += " is-missing";
      body.appendChild(el("p", null, ["Recorded error: ", el("span", { class: "mono", text: str(pred.error) })]));
    } else {
      badgeText = pred.label ? str(pred.label) : pred.abstained ? "Abstained" : "No label";
      if (!pred.label) badgeClass += " is-missing";
      if (pred.abstained && pred.label) body.appendChild(el("p", null, el("strong", { text: "Marked as an abstention." })));
      if (!pred.label) body.appendChild(el("p", { class: "note small", text: "No label was recorded, so this output is not compared with the reference." }));
      if (pred.explanation) body.appendChild(el("p", { text: str(pred.explanation) }));
      if (Array.isArray(pred.evidence) && pred.evidence.length) {
        body.appendChild(el("p", { class: "small note", text: "Evidence cited:" }));
        body.appendChild(el("ul", { class: "small" }, pred.evidence.map(function (e) { return el("li", { class: "mono", text: str(e) }); })));
      }
    }
    if (cmp.state !== "none") badgeClass += cmp.state === "match" ? " is-match" : " is-mismatch";

    return el("div", { class: "judgement" }, [
      el("div", { class: "jhead" }, [
        el("span", { class: badgeClass }, [el("span", { class: "method", text: method }), badgeText]),
        el("span", { class: "chip", text: METHOD_NAMES[method] }),
        cmp.state === "match" ? el("span", { class: "cmp is-match", text: "✓ matches reference" }) : null,
        cmp.state === "mismatch" ? el("span", { class: "cmp is-mismatch", text: "✗ differs from reference" }) : null
      ]),
      body.childNodes.length ? body : null
    ]);
  }

  function renderDetail(c, moveFocus) {
    C.clear(detailEl);
    if (!c) {
      detailEl.appendChild(el("p", { class: "note", text: "Select a case to see its evidence, reference label and recorded outputs." }));
      return;
    }
    var ref = refLabel(c);
    var preds = C.isObject(c.predictions) ? c.predictions : {};
    var tree = C.treeUrl(c.repo, c.commit);
    var loaded = Array.isArray(c.loaded_set) ? c.loaded_set : [];

    var heading = el("h2", { id: "detail-title", tabindex: "-1", text: c.case_id });
    detailEl.appendChild(el("div", { class: "detail-head" }, [
      heading,
      el("div", { class: "crow" }, [
        el("span", { class: "chip", text: stratumName(c.stratum) }),
        c.parent_case_id ? el("span", { class: "chip", text: "variant of " + str(c.parent_case_id) }) : null,
        c.changed_property ? el("span", { class: "chip", text: "changed: " + str(c.changed_property).replace(/_/g, " ") }) : null
      ])
    ]));

    var kv = el("dl", { class: "kv" }, [
      kvRow("Task", [str(c.task) || "not recorded", c.task_origin ? el("span", { class: "note small", text: " (" + str(c.task_origin) + ")" }) : null]),
      kvRow("Target", el("span", { class: "mono", text: str(c.target_path) || "not recorded" })),
      kvRow("Repository", tree
        ? [el("a", { href: tree, class: "mono ext", text: str(c.repo) + " @ " + C.shortCommit(c.commit) })]
        : el("span", { class: "mono", text: str(c.repo) || "not recorded" })),
      kvRow("License", str(c.license) || "not recorded"),
      kvRow("Loaded set", loaded.length
        ? el("ul", { class: "mono-list" }, loaded.map(function (p) { return el("li", { text: str(p) }); }))
        : "empty or not recorded")
    ]);
    detailEl.appendChild(el("section", { "aria-labelledby": "d-task" }, [el("h3", { id: "d-task", text: "Task and target" }), kv]));

    detailEl.appendChild(el("section", { "aria-labelledby": "d-spans" }, [
      el("h3", { id: "d-spans", text: "Source spans" }),
      el("div", { class: "span-stack" }, [spanPanel("Rule A", c.rule_a, c), spanPanel("Rule B", c.rule_b, c)])
    ]));

    detailEl.appendChild(el("section", { "aria-labelledby": "d-ref" }, [
      el("h3", { id: "d-ref", text: "Reference label" }),
      referenceBlock(c)
    ]));

    detailEl.appendChild(el("section", { "aria-labelledby": "d-pred" }, [
      el("h3", { id: "d-pred", text: "Recorded method outputs" }),
      ref ? null : el("p", { class: "note small", text: "No reference label: profile P1 does not fix this case and no human labels exist, so outputs are not compared." }),
      el("div", { class: "judgements" }, METHODS.map(function (m) { return predictionBlock(m, preds[m] || null, ref); }))
    ]));

    if (moveFocus) heading.focus();
  }

  function idFromHash() {
    var m = /^#case=(.+)$/.exec(location.hash || "");
    if (!m) return null;
    try { return decodeURIComponent(m[1]); } catch (e) { return null; }
  }

  function selectFromHash(moveFocus) {
    var id = idFromHash();
    if (id && state.byId[id]) {
      state.currentId = id;
    } else if (!state.currentId) {
      var first = filtered()[0];
      state.currentId = first ? first.case_id : null;
    }
    renderList();
    renderDetail(state.byId[state.currentId] || null, moveFocus && !!id);
  }

  // ----- boot -----------------------------------------------------------------

  function render(data) {
    C.clear(root);
    if (!C.isObject(data)) { root.appendChild(contractError("The file is not a JSON object.")); return; }
    if (data.available !== true) { root.appendChild(unavailable(data.reason)); return; }
    if (!Array.isArray(data.cases)) { root.appendChild(contractError("\"available\" is true but \"cases\" is not an array.")); return; }

    var skipped = 0;
    data.cases.forEach(function (c) {
      if (!C.isObject(c) || typeof c.case_id !== "string" || !c.case_id || state.byId[c.case_id]) { skipped++; return; }
      state.cases.push(c);
      state.byId[c.case_id] = c;
    });
    if (!state.cases.length) {
      root.appendChild(el("div", { class: "message" }, [el("h2", { text: "No recorded cases" }), el("p", { text: "The export is marked available but contains no cases." })]));
      return;
    }

    countEl = el("p", { class: "count-line", "aria-live": "polite" });
    listEl = el("ul", { class: "case-list", "aria-label": "Cases" });
    detailEl = el("article", { class: "detail panel", "aria-labelledby": "detail-title" });

    root.appendChild(el("div", { class: "cases-layout" }, [
      el("div", null, [
        el("h2", { class: "visually-hidden", text: "Case list" }),
        buildFilters(),
        countEl,
        skipped ? el("p", { class: "note small", text: skipped + " malformed or duplicate entries were skipped." }) : null,
        listEl
      ]),
      detailEl
    ]));

    window.addEventListener("hashchange", function () { selectFromHash(true); });
    selectFromHash(false);
  }

  C.loadData("replay", "../").then(function (result) {
    if (!result.ok) {
      C.clear(root);
      root.appendChild(C.loadErrorMessage("data/replay.json", result));
      return;
    }
    render(result.data);
  });
})();
