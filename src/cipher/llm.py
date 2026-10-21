"""Configurable model adapter: clean, stateless chat requests to a local Ollama server.

Each request contains only a method prompt and the evidence packet. Responses are validated against a JSON schema;
failures are retried a bounded number of times with a recorded seed change and otherwise returned as explicit errors.
Every attempt is logged (model digest, options, token counts, latency, raw text).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

import requests

OLLAMA = "http://localhost:11434"


@dataclass
class ModelConfig:
    provider: str = "ollama"
    model: str = "qwen3.6:35b-a3b"
    digest: str = "a7eb95c53bcf96b4bdd008d0fab4a5dac88047d9c1a7a9ab88ed453423fbd87c"
    think: bool = True
    temperature: float = 0.6
    top_p: float = 0.95
    top_k: int = 20
    seed: int = 20261021
    num_ctx: int = 16384
    num_predict: int = 8192
    max_retries: int = 2
    timeout_s: int = 900

    def options(self, attempt: int) -> dict:
        return {"temperature": self.temperature, "top_p": self.top_p, "top_k": self.top_k,
                "seed": self.seed + attempt, "num_ctx": self.num_ctx, "num_predict": self.num_predict}


@dataclass
class CallResult:
    ok: bool
    data: dict | None
    error: str | None
    attempts: list[dict] = field(default_factory=list)

    @property
    def input_tokens(self) -> int:
        return sum(a.get("input_tokens") or 0 for a in self.attempts)

    @property
    def output_tokens(self) -> int:
        return sum(a.get("output_tokens") or 0 for a in self.attempts)

    @property
    def latency_s(self) -> float:
        return round(sum(a.get("latency_s") or 0 for a in self.attempts), 2)


def installed_digest(model: str) -> str | None:
    tags = requests.get(f"{OLLAMA}/api/tags", timeout=30).json()
    for m in tags.get("models", []):
        if m["name"] == model:
            return m["digest"]
    return None


def check_model(cfg: ModelConfig) -> None:
    """Refuse to run if the installed model is missing or its digest differs from the pinned one."""
    d = installed_digest(cfg.model)
    if d != cfg.digest:
        raise RuntimeError(f"model {cfg.model} digest {d} does not match pinned {cfg.digest}")


def validate(data: Any, schema: dict) -> str | None:
    """Minimal JSON-schema check (types, required keys, enums) sufficient for the method schemas."""
    def walk(v: Any, s: dict, path: str) -> str | None:
        t = s.get("type")
        types = t if isinstance(t, list) else [t]
        pytypes = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None),
                   "integer": int, "number": (int, float)}
        if t and not any(isinstance(v, pytypes[x]) for x in types):
            return f"{path}: expected {t}"
        if "enum" in s and v not in s["enum"]:
            return f"{path}: {v!r} not in enum"
        if isinstance(v, dict):
            for k in s.get("required", []):
                if k not in v:
                    return f"{path}.{k}: missing"
            for k, sub in s.get("properties", {}).items():
                if k in v:
                    e = walk(v[k], sub, f"{path}.{k}")
                    if e:
                        return e
        if isinstance(v, list) and "items" in s:
            for i, x in enumerate(v):
                e = walk(x, s["items"], f"{path}[{i}]")
                if e:
                    return e
        return None
    return walk(data, schema, "$")


def chat(cfg: ModelConfig, system: str, user: str, schema: dict) -> CallResult:
    attempts = []
    for attempt in range(cfg.max_retries + 1):
        body = {"model": cfg.model, "stream": False, "think": cfg.think, "format": schema,
                "options": cfg.options(attempt),
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        rec = {"attempt": attempt, "seed": cfg.seed + attempt,
               "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()}
        t = time.time()
        try:
            r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=cfg.timeout_s)
            rec["latency_s"] = round(time.time() - t, 2)
            r.raise_for_status()
            resp = r.json()
        except Exception as exc:  # network or server failure
            rec.update(status="api_error", error=str(exc)[:300])
            attempts.append(rec)
            continue
        msg = resp.get("message", {})
        rec.update(input_tokens=resp.get("prompt_eval_count"), output_tokens=resp.get("eval_count"),
                   done_reason=resp.get("done_reason"), model=resp.get("model"),
                   raw=msg.get("content", ""), thinking_chars=len(msg.get("thinking") or ""))
        if resp.get("done_reason") == "length":
            rec.update(status="truncated", error="output hit num_predict")
            attempts.append(rec)
            continue
        try:
            data = json.loads(msg.get("content", ""))
        except json.JSONDecodeError as exc:
            rec.update(status="malformed", error=f"invalid JSON: {exc}")
            attempts.append(rec)
            continue
        err = validate(data, schema)
        if err:
            rec.update(status="schema_violation", error=err)
            attempts.append(rec)
            continue
        rec["status"] = "ok"
        attempts.append(rec)
        return CallResult(True, data, None, attempts)
    return CallResult(False, None, attempts[-1].get("status", "error") if attempts else "error", attempts)
