from __future__ import annotations

import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsCollector:
    started_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _counters: Counter[str] = field(default_factory=Counter)
    _latency_ms: list[int] = field(default_factory=list)

    def record_success(self, page_type: str, crawl_ms: int) -> None:
        with self._lock:
            self._counters["crawl_total"] += 1
            self._counters["crawl_success_total"] += 1
            self._counters[f"page_type_{page_type}_total"] += 1
            self._latency_ms.append(crawl_ms)
            self._trim_latencies()

    def record_error(self, code: str) -> None:
        with self._lock:
            self._counters["crawl_total"] += 1
            self._counters["crawl_error_total"] += 1
            self._counters[f"crawl_error_{code}_total"] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies = sorted(self._latency_ms)
            return {
                "uptime_seconds": int(time.time() - self.started_at),
                "counters": dict(self._counters),
                "latency_ms": {
                    "count": len(latencies),
                    "p50": _percentile(latencies, 0.50),
                    "p95": _percentile(latencies, 0.95),
                    "max": latencies[-1] if latencies else 0,
                },
            }

    def _trim_latencies(self) -> None:
        if len(self._latency_ms) > 1000:
            self._latency_ms[:] = self._latency_ms[-1000:]


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    index = min(len(values) - 1, round((len(values) - 1) * percentile))
    return values[index]


metrics = MetricsCollector()
