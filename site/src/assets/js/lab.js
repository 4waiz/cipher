/*
 * Case Lab UI. Authored illustration of the declared profile.
 * The label is computed by CipherProfile.evaluate (assets/js/profile.js) from the
 * ancestor chain and file depths; nothing here is a lookup table of outcomes.
 */
(function () {
  "use strict";

  var P = window.CipherProfile;
  var C = window.Cipher;
  if (!P || !C) return;
  var el = C.el;

  var form = document.getElementById("lab-controls");
  if (!form) return;

  // ----- Authored scenario (fixed wording) -----------------------------------

  var RULE_TEXT = {
    A: "Use exactly four spaces per indentation level.",
    B: "Use exactly two spaces per indentation level."
  };
  var DECISION = "indentation width";
  var VALUE_WORDS = { 4: "four spaces", 2: "two spaces" };
  var SOURCE_FILES = ["web/src/button.ts", "api/src/server.ts", "scripts/build.ts"];
  var FOLDER_TITLES = { web: "Web package", api: "API package" };

  /** Build the authored repository for a placement of Rule B. */
  function buildScenario(placement) {
    var contents = {};
    var rootLines = ["# Project conventions", "", "## Formatting", RULE_TEXT.A];
    var ruleA = { id: "A", path: "AGENTS.md", line: 4, decision: DECISION, value: 4 };
    var ruleB;
    if (placement === "root") {
      rootLines.push("", "## Editor settings", RULE_TEXT.B);
      ruleB = { id: "B", path: "AGENTS.md", line: rootLines.length, decision: DECISION, value: 2 };
    } else {
      var nested = ["# " + FOLDER_TITLES[placement] + " conventions", "", "## Formatting", RULE_TEXT.B];
      ruleB = { id: "B", path: placement + "/AGENTS.md", line: 4, decision: DECISION, value: 2 };
      contents[ruleB.path] = nested;
    }
    contents["AGENTS.md"] = rootLines;
    var files = Object.keys(contents).concat(SOURCE_FILES);
    return { files: files, contents: contents, rules: [ruleA, ruleB] };
  }

  // ----- Small formatting helpers ---------------------------------------------

  function dirLabel(dir) { return dir === "" ? "/ (root)" : dir + "/"; }
  function code(text) { return el("code", { class: "code-inline", text: text }); }
  function ruleById(rules, id) { return rules[0].id === id ? rules[0] : rules[1]; }
  function depthWords(d) { return d === 0 ? "depth 0 (root)" : "depth " + d; }

  // ----- Panels ---------------------------------------------------------------

  function buildTree(files) {
    var root = { name: "", path: "", type: "dir", children: {} };
    files.forEach(function (f) {
      var parts = f.split("/");
      var node = root;
      for (var i = 0; i < parts.length; i++) {
        var isFile = i === parts.length - 1;
        var path = parts.slice(0, i + 1).join("/");
        if (!node.children[parts[i]]) {
          node.children[parts[i]] = { name: parts[i], path: path, type: isFile ? "file" : "dir", children: {} };
        }
        node = node.children[parts[i]];
      }
    });
    return root;
  }

  function sortedChildren(node) {
    return Object.keys(node.children).map(function (k) { return node.children[k]; }).sort(function (a, b) {
      var rank = function (n) { return n.name === "AGENTS.md" ? 0 : n.type === "dir" ? 1 : 2; };
      return rank(a) - rank(b) || a.name.localeCompare(b.name);
    });
  }

  function renderTree(scenario, res) {
    var tree = buildTree(scenario.files);
    var rules = scenario.rules;

    function nodeEl(node) {
      var classes = ["tree-node"];
      var tags = [];
      if (node.type === "dir" && res.chain.indexOf(node.path) !== -1) {
        classes.push("on-chain");
        tags.push(el("span", { class: "tag", text: "on chain" }));
      }
      if (node.type === "file" && node.path === res.target) {
        classes.push("is-target");
        tags.push(el("span", { class: "tag", text: "target" }));
      }
      if (node.type === "file" && P.isContextFile(node.path)) {
        var loaded = res.loaded.indexOf(node.path) !== -1;
        classes.push(loaded ? "ctx-loaded" : "ctx-unloaded");
        tags.push(el("span", { class: "tag", text: loaded ? "loaded" : "not loaded" }));
        rules.forEach(function (r) {
          if (r.path === node.path) tags.push(el("span", { class: "tag", text: "Rule " + r.id + " · line " + r.line }));
        });
      }
      var glyph = node.type === "dir" ? "▸" : P.isContextFile(node.path) ? "§" : "·";
      var label = node.path === "" ? "repository root/" : node.name + (node.type === "dir" ? "/" : "");
      var li = el("li", null, [
        el("div", { class: classes.join(" ") }, [
          el("span", { class: "glyph", "aria-hidden": "true", text: glyph }),
          el("span", { text: label }),
          tags
        ])
      ]);
      var kids = sortedChildren(node);
      if (kids.length) li.appendChild(el("ul", null, kids.map(nodeEl)));
      return li;
    }

    var panel = document.getElementById("lab-tree");
    C.clear(panel);
    panel.appendChild(el("h3", { id: "lab-tree-title", text: "Repository" }));
    panel.appendChild(el("ul", { class: "tree", "aria-label": "Repository tree; the target's ancestor chain and loaded AGENTS.md files are marked" }, [nodeEl(tree)]));
    panel.appendChild(el("p", { class: "legend", "aria-hidden": "true" }, [
      el("span", { class: "lg-chain", text: "ancestor chain" }),
      el("span", { class: "lg-target", text: "target" }),
      el("span", { class: "lg-loaded", text: "loaded AGENTS.md" })
    ]));
  }

  function applicabilityReason(rule, app, res) {
    var dir = P.dirOf(rule.path);
    if (app.active) {
      if (dir === "") return ["Root ", code("AGENTS.md"), " is on every target's ancestor chain, so it is loaded."];
      return [code(rule.path), " is in ", code(dir + "/"), ", which is on the ancestor chain of ", code(res.target), ", so it is loaded."];
    }
    if (app.reason === "off-chain") {
      return [code(rule.path), " is in ", code(dir + "/"), ", which is not an ancestor of ", code(res.target), ". The file is not loaded, so the rule is inactive."];
    }
    if (app.reason === "condition-excludes") return ["The rule's condition excludes this task, so it is inactive."];
    if (app.reason === "not-context-file") return [code(rule.path), " is not an AGENTS.md file and does not participate."];
    return ["Inactive."];
  }

  function renderApplicability(scenario, res) {
    var panel = document.getElementById("lab-applicability");
    C.clear(panel);
    panel.appendChild(el("h3", { id: "lab-app-title", text: "Applicability" }));

    var chainEl = el("span", { class: "chain" });
    res.chain.forEach(function (d, i) {
      if (i) chainEl.appendChild(el("span", { class: "sep", "aria-hidden": "true", text: "→" }));
      chainEl.appendChild(el("span", { text: dirLabel(d) }));
    });

    var rows = [
      el("div", null, [el("dt", { text: "Target" }), el("dd", null, el("span", { class: "mono", text: res.target }))]),
      el("div", null, [el("dt", { text: "Ancestor chain" }), el("dd", null, chainEl)])
    ];
    if (res.loaded.length || res.steps[0].status === "pass") {
      rows.push(el("div", null, [
        el("dt", { text: "Loaded set (binding AGENTS.md files)" }),
        el("dd", null, el("ul", { class: "mono-list" }, res.loaded.map(function (f) {
          return el("li", { text: f + "  · " + depthWords(P.depthOf(P.dirOf(f))) });
        })))
      ]));
    }
    scenario.rules.forEach(function (r) {
      var app = res.applicability[r.id];
      if (!app) return;
      rows.push(el("div", null, [
        el("dt", { text: "Rule " + r.id }),
        el("dd", null, [
          el("span", { class: "state " + (app.active ? "state-on" : "state-off"), text: app.active ? "Active. " : "Inactive. " }),
          applicabilityReason(r, app, res)
        ])
      ]));
    });
    panel.appendChild(el("dl", { class: "facts" }, rows));
  }

  function renderPrecedence(scenario, res) {
    var panel = document.getElementById("lab-precedence");
    C.clear(panel);
    panel.appendChild(el("h3", { id: "lab-prec-title", text: "Precedence" }));
    var a = scenario.rules[0];
    var b = scenario.rules[1];

    if (!res.precedence) {
      var why;
      if (res.label === "Disjoint applicability") {
        var off = scenario.rules.filter(function (r) { return !res.applicability[r.id].active; }).map(function (r) { return "Rule " + r.id; });
        why = ["Not reached. ", off.join(" and "), " is not in the loaded set for this target, so there is nothing to rank."];
      } else if (res.label === "Compatible") {
        why = ["Not reached. The rules do not demand different outcomes, so no ranking is needed."];
      } else {
        why = ["Not reached. The evidence is insufficient to compare the rules."];
      }
      panel.appendChild(el("p", { class: "verdict" }, why));
      panel.appendChild(el("p", { class: "note small", text: "Precedence is compared only when both rules are loaded and incompatible." }));
      return;
    }

    [a, b].forEach(function (r) {
      panel.appendChild(el("div", { class: "depth-row" }, [
        el("span", null, ["Rule " + r.id + " ", code(r.path + ":" + r.line)]),
        el("span", { class: "note", text: depthWords(P.depthOf(P.dirOf(r.path))) })
      ]));
    });

    if (res.precedence.relation === "equal") {
      var first = a.line < b.line ? a : b;
      var second = first === a ? b : a;
      panel.appendChild(el("p", { class: "verdict strong" }, [
        el("strong", { text: "Equal authority — no winner. " }),
        res.precedence.sameFile
          ? ["Both rules come from ", code(a.path), ". Rule " + first.id + " appearing first (line " + first.line + ", before line " + second.line + ") does not decide between them."]
          : ["Both files sit at the same depth. Display order does not decide between them."]
      ]));
    } else {
      var w = ruleById(scenario.rules, res.precedence.winner);
      var l = ruleById(scenario.rules, res.precedence.loser);
      panel.appendChild(el("p", { class: "verdict strong" }, [
        el("strong", null, [code(w.path), " is deeper on the chain. "]),
        "Rule " + w.id + " overrides Rule " + l.id + " for this target; other requirements in ",
        code(l.path), " stay in effect."
      ]));
    }
  }

  function renderSpans(scenario, res) {
    var wrap = document.getElementById("lab-spans");
    C.clear(wrap);
    scenario.rules.forEach(function (r) {
      var lines = scenario.contents[r.path] || [];
      var app = res.applicability[r.id];
      var loaded = app ? app.active : null;
      var pre = el("pre", { class: "code", tabindex: "0", "aria-label": r.path + ", " + lines.length + " lines, rule on line " + r.line });
      lines.forEach(function (text, i) {
        var n = i + 1;
        pre.appendChild(el("span", { class: "line" + (n === r.line ? " hl" : "") }, [
          el("span", { class: "ln", "aria-hidden": "true", text: String(n) }),
          el("span", { class: "tx", text: text || " " })
        ]));
      });
      wrap.appendChild(el("section", { class: "evidence", "aria-label": "Rule " + r.id + " source span" }, [
        el("div", { class: "evidence-head" }, [
          el("span", null, [
            el("span", { class: "who", text: "Rule " + r.id + "  " }),
            el("span", { class: "where", text: r.path + ":" + r.line })
          ]),
          loaded === null ? null : el("span", { class: "span-status" + (loaded ? " on" : ""), text: loaded ? "loaded for target" : "not loaded for target" })
        ]),
        pre
      ]));
    });
  }

  var STEP_TITLES = {
    evidence: "Evidence sufficiency",
    applicability: "Initial joint applicability",
    incompatibility: "Incompatibility for the same decision",
    priority: "Priority resolution"
  };

  function stepDetail(s, scenario, res) {
    var a = scenario.rules[0];
    var b = scenario.rules[1];
    if (s.status === "skip") return "Not reached.";
    switch (s.key) {
      case "evidence":
        return s.status === "pass"
          ? "Both source spans and the target path are known."
          : "Missing: " + (s.missing || []).join(", ") + ".";
      case "applicability":
        if (s.status === "pass") return "Both rules are in the loaded set for this target.";
        return s.inactive.map(function (id) { return "Rule " + id; }).join(" and ") + " is inactive for this target, so the rules never meet.";
      case "incompatibility":
        if (s.status === "pass") return "Both set the " + DECISION + ": " + VALUE_WORDS[a.value] + " versus " + VALUE_WORDS[b.value] + ". They cannot both hold.";
        return "The rules do not demand different outcomes for the same decision.";
      case "priority":
        if (s.relation === "equal") return "Same authority; display order does not pick a winner.";
        var w = ruleById(scenario.rules, s.winner);
        return w.path + " is deeper on the ancestor chain, so Rule " + w.id + " wins.";
    }
    return "";
  }

  function statusText(s, res) {
    if (s.status === "pass") return "passed";
    if (s.status === "skip") return "not reached";
    return "→ " + res.label;
  }

  function explanation(scenario, res) {
    var a = scenario.rules[0];
    var b = scenario.rules[1];
    switch (res.label) {
      case "Valid override":
        var w = ruleById(scenario.rules, res.winner);
        var l = w === a ? b : a;
        return ["Both rules are loaded for ", code(res.target), " and set the " + DECISION + " to different values. ",
          code(w.path), " is deeper on the target's ancestor chain than ", code(l.path),
          ", so Rule " + w.id + " overrides Rule " + l.id + " for this file."];
      case "Disjoint applicability":
        var off = scenario.rules.filter(function (r) { return !res.applicability[r.id].active; });
        var on = scenario.rules.filter(function (r) { return res.applicability[r.id].active; });
        return [off.map(function (r) { return "Rule " + r.id; }).join(" and "), " lives in ", code(off[0].path),
          ", whose folder is not on the ancestor chain of ", code(res.target), ". It is not loaded for this edit, so the two rules never apply together",
          on.length ? "; only Rule " + on[0].id + " governs this file." : "."];
      case "Unresolved conflict":
        return ["Both rules are loaded for ", code(res.target), " and set the " + DECISION + " to different values, but they have equal authority",
          res.precedence && res.precedence.sameFile ? [" (both in ", code(a.path), ")"] : "",
          ". The profile does not let display order pick a winner, so the contradiction stays unresolved and should be surfaced rather than settled silently."];
      case "Compatible":
        return ["Both rules apply to ", code(res.target), " and can be satisfied together."];
      default:
        return ["The available evidence does not support a decision."];
    }
  }

  function effectiveText(scenario, res) {
    if (res.label === "Unresolved conflict") return "none determined; the profile leaves this contradiction open.";
    if (res.label === "Insufficient evidence") return "cannot be determined from the evidence.";
    return res.effective.map(function (id) {
      var r = ruleById(scenario.rules, id);
      return VALUE_WORDS[r.value] + " (Rule " + id + ", " + r.path + ")";
    }).join(" and ") + ".";
  }

  function renderResult(scenario, res) {
    var panel = document.getElementById("lab-result");
    C.clear(panel);
    panel.appendChild(el("h3", { class: "panel-title", id: "lab-result-title", text: "Resulting label" }));
    panel.appendChild(el("div", { class: "result-label-row" }, [
      el("p", { class: "result-label", text: res.label }),
      el("span", { class: "result-context" }, ["Rule B in ", code(scenario.rules[1].path), " · target ", code(res.target)])
    ]));
    panel.appendChild(el("p", { class: "result-explanation" }, explanation(scenario, res)));
    panel.appendChild(el("p", { class: "effective" }, [el("strong", { text: "Indentation for this edit: " }), effectiveText(scenario, res)]));

    var list = el("ol", { class: "steps", "aria-label": "Decision sequence" });
    res.steps.forEach(function (s) {
      list.appendChild(el("li", { class: "step is-" + s.status }, [
        el("span", { class: "step-title" }, [STEP_TITLES[s.key], el("span", { class: "step-status", text: statusText(s, res) })]),
        el("span", { class: "step-detail", text: stepDetail(s, scenario, res) })
      ]));
    });
    panel.appendChild(list);
  }

  // ----- Wiring ---------------------------------------------------------------

  function currentValue(name, fallback) {
    var checked = form.querySelector('input[name="' + name + '"]:checked');
    return checked ? checked.value : fallback;
  }

  function update(announce) {
    var placement = currentValue("placement", "web");
    var target = currentValue("target", "web/src/button.ts");
    var scenario = buildScenario(placement);
    var res = P.evaluate({ files: scenario.files, target: target, task: { kind: "add helper function" }, rules: scenario.rules });

    renderResult(scenario, res);
    renderTree(scenario, res);
    renderApplicability(scenario, res);
    renderPrecedence(scenario, res);
    renderSpans(scenario, res);

    var mini = document.getElementById("lab-mini");
    if (mini) {
      C.clear(mini);
      C.appendAll(mini, ["Label: ", el("strong", { text: res.label }), " · ", el("a", { href: "#lab-result", tabindex: "-1", text: "see why" })]);
    }

    if (announce) {
      var live = document.getElementById("lab-announce");
      if (live) live.textContent = "Label: " + res.label + ". Rule B in " + scenario.rules[1].path + ", target " + target + ".";
    }
  }

  form.addEventListener("change", function () { update(true); });
  update(false);
})();
