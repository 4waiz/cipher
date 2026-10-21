/*
 * CIPHER declared profile, as fixed rules for the Case Lab illustration.
 *
 * This is NOT the research pipeline and NOT a model. It encodes the declared
 * profile so the Case Lab can show how a label follows from the decision sequence:
 *   1. evidence sufficiency
 *   2. initial joint applicability
 *   3. incompatibility for the same decision
 *   4. priority resolution
 *
 * Profile (frozen experimental interpretation, grounded in https://agents.md/):
 *   - only root and nested AGENTS.md files participate;
 *   - the binding loaded set for a target is the AGENTS.md files on its ancestor chain;
 *   - a deeper applicable file overrides an incompatible ancestor instruction;
 *   - equal-authority contradictions (same file or same depth) are not resolved by display order;
 *   - instructions from unrelated branches are not loaded.
 *
 * Classic script (no ES module syntax) so it also runs from file://.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    root.CipherProfile = api;
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var LABELS = [
    "Unresolved conflict",
    "Valid override",
    "Disjoint applicability",
    "Compatible",
    "Insufficient evidence"
  ];

  var CONTEXT_FILE = "AGENTS.md";

  function normalize(path) {
    return String(path || "")
      .replace(/\\/g, "/")
      .replace(/^\.\//, "")
      .replace(/\/+/g, "/")
      .replace(/^\/|\/$/g, "");
  }

  /** Directory containing a path ("" is the repository root). */
  function dirOf(path) {
    var p = normalize(path);
    var i = p.lastIndexOf("/");
    return i < 0 ? "" : p.slice(0, i);
  }

  /** Number of directory levels below the root ("" -> 0, "web" -> 1, "web/src" -> 2). */
  function depthOf(dir) {
    var d = normalize(dir);
    return d === "" ? 0 : d.split("/").length;
  }

  /** Directories from the root down to the target's own folder, root first. */
  function ancestorChain(targetPath) {
    var parts = normalize(targetPath).split("/");
    parts.pop();
    var chain = [""];
    for (var i = 0; i < parts.length; i++) {
      if (parts[i]) chain.push(parts.slice(0, i + 1).join("/"));
    }
    return chain;
  }

  function isContextFile(path) {
    var p = normalize(path);
    return p === CONTEXT_FILE || p.slice(-(CONTEXT_FILE.length + 1)) === "/" + CONTEXT_FILE;
  }

  /** AGENTS.md files whose folder lies on the target's ancestor chain, shallowest first. */
  function loadedSet(files, targetPath) {
    var chain = ancestorChain(targetPath);
    return files
      .map(normalize)
      .filter(isContextFile)
      .filter(function (f) { return chain.indexOf(dirOf(f)) !== -1; })
      .sort(function (a, b) { return depthOf(dirOf(a)) - depthOf(dirOf(b)); });
  }

  /**
   * Applicability of one rule for a target and task.
   * reason codes: "loaded" | "not-context-file" | "off-chain" | "condition-excludes"
   */
  function applicability(rule, loaded, target, task) {
    var path = normalize(rule.path);
    if (!isContextFile(path)) {
      return { active: false, reason: "not-context-file", path: path };
    }
    if (loaded.indexOf(path) === -1) {
      return { active: false, reason: "off-chain", path: path };
    }
    if (typeof rule.condition === "function" && !rule.condition(target, task)) {
      return { active: false, reason: "condition-excludes", path: path };
    }
    return { active: true, reason: "loaded", path: path };
  }

  /** Two rules are incompatible when they set the same decision to different values. */
  function incompatible(a, b) {
    return a.decision === b.decision && a.value !== b.value;
  }

  /**
   * Evaluate a pair of rules for one target under the declared profile.
   * input: { files: [path], target: path, task: any, rules: [ruleA, ruleB] }
   * rule:  { id, path, line, decision, value, condition? }
   */
  function evaluate(input) {
    var files = (input.files || []).map(normalize);
    var target = normalize(input.target);
    var rules = input.rules || [];
    var a = rules[0];
    var b = rules[1];

    var result = {
      label: null,
      target: target,
      chain: ancestorChain(target),
      loaded: [],
      applicability: {},
      incompatible: null,
      precedence: null,
      winner: null,
      effective: [],
      steps: []
    };

    function step(key, status, info) {
      var s = { key: key, status: status };
      if (info) for (var k in info) if (Object.prototype.hasOwnProperty.call(info, k)) s[k] = info[k];
      result.steps.push(s);
    }
    function skipRemaining(fromIndex) {
      var keys = ["evidence", "applicability", "incompatibility", "priority"];
      for (var i = fromIndex; i < keys.length; i++) step(keys[i], "skip");
    }

    // 1. Evidence sufficiency: both source spans and the target must be known.
    var missing = [];
    if (!target || files.indexOf(target) === -1) missing.push("target");
    [a, b].forEach(function (r, i) {
      var name = i === 0 ? "A" : "B";
      if (!r || !r.path || files.indexOf(normalize(r.path)) === -1 || !r.line) missing.push("rule " + name + " source span");
      else if (r.decision === undefined || r.value === undefined) missing.push("rule " + name + " content");
    });
    if (missing.length) {
      step("evidence", "stop", { missing: missing });
      skipRemaining(1);
      result.label = "Insufficient evidence";
      return result;
    }
    step("evidence", "pass");

    // 2. Initial joint applicability: both rules must be active for this target and task.
    result.loaded = loadedSet(files, target);
    var appA = applicability(a, result.loaded, target, input.task);
    var appB = applicability(b, result.loaded, target, input.task);
    result.applicability[a.id] = appA;
    result.applicability[b.id] = appB;
    if (!appA.active || !appB.active) {
      var inactive = [];
      if (!appA.active) inactive.push(a.id);
      if (!appB.active) inactive.push(b.id);
      step("applicability", "stop", { inactive: inactive });
      skipRemaining(2);
      result.label = "Disjoint applicability";
      result.effective = [a, b].filter(function (r) { return result.applicability[r.id].active; })
        .map(function (r) { return r.id; });
      return result;
    }
    step("applicability", "pass");

    // 3. Incompatibility for the same decision.
    result.incompatible = incompatible(a, b);
    if (!result.incompatible) {
      step("incompatibility", "stop", { sameDecision: a.decision === b.decision });
      skipRemaining(3);
      result.label = "Compatible";
      result.effective = [a.id, b.id];
      return result;
    }
    step("incompatibility", "pass", { decision: a.decision });

    // 4. Priority resolution: the deeper file on the ancestor chain wins; equal depth has no winner.
    var dA = depthOf(dirOf(a.path));
    var dB = depthOf(dirOf(b.path));
    var sameFile = normalize(a.path) === normalize(b.path);
    if (dA === dB) {
      result.precedence = { relation: "equal", sameFile: sameFile, depths: [dA, dB] };
      step("priority", "stop", { relation: "equal" });
      result.label = "Unresolved conflict";
      result.effective = [];
      return result;
    }
    var winner = dA > dB ? a : b;
    var loser = winner === a ? b : a;
    result.precedence = { relation: "deeper", sameFile: false, depths: [dA, dB], winner: winner.id, loser: loser.id };
    result.winner = winner.id;
    step("priority", "stop", { relation: "deeper", winner: winner.id });
    result.label = "Valid override";
    result.effective = [winner.id];
    return result;
  }

  return {
    LABELS: LABELS,
    normalize: normalize,
    dirOf: dirOf,
    depthOf: depthOf,
    ancestorChain: ancestorChain,
    isContextFile: isContextFile,
    loadedSet: loadedSet,
    evaluate: evaluate
  };
});
