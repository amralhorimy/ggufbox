"""RAM awareness: what is free (container-aware) and what a model load is likely to cost."""
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

MB = 1024**2


def _read_int(path: str) -> int | None:
    try:
        raw = Path(path).read_text().strip()
        return None if raw == "max" else int(raw)
    except (OSError, ValueError):
        return None


def memory_snapshot() -> dict:
    """System memory, clamped to the cgroup limit when running in a memory-limited container."""
    vm = psutil.virtual_memory()
    total, available = vm.total, vm.available
    limit = _read_int("/sys/fs/cgroup/memory.max") or _read_int("/sys/fs/cgroup/memory/memory.limit_in_bytes")
    limited = bool(limit and limit < vm.total)
    if limited:
        used = _read_int("/sys/fs/cgroup/memory.current") or _read_int("/sys/fs/cgroup/memory/memory.usage_in_bytes") or 0
        total, available = limit, min(available, max(limit - used, 0))
    rss = psutil.Process(os.getpid()).memory_info().rss
    return {"total": total, "available": available, "process_rss": rss, "container_limited": limited}


@dataclass
class MemoryEstimate:
    model_bytes: int
    kv_cache_bytes: int
    overhead_bytes: int

    @property
    def total_bytes(self) -> int:
        return self.model_bytes + self.kv_cache_bytes + self.overhead_bytes

    def as_dict(self) -> dict:
        return {**asdict(self), "total_bytes": self.total_bytes}


def estimate_memory(model_bytes: int, n_ctx: int, n_gpu_layers: int = 0, mmproj_bytes: int = 0) -> MemoryEstimate:
    """Heuristic RAM cost of a load. The KV-cache term assumes a typical GQA model
    (~32 MB per 1k tokens per GB of weights) and is deliberately a little pessimistic."""
    kv = model_bytes / 1e9 * 32 * MB * (n_ctx / 1024)
    weights = model_bytes + mmproj_bytes
    gpu_share = 0.15 if n_gpu_layers == -1 else (0.6 if n_gpu_layers > 0 else 1.0)
    return MemoryEstimate(int(weights * gpu_share), int(kv * gpu_share), 400 * MB)


def check_fit(estimate: MemoryEstimate, budget_fraction: float) -> dict:
    snap = memory_snapshot()
    budget = int(snap["available"] * budget_fraction)
    return {
        "fits": estimate.total_bytes <= budget,
        "estimated_bytes": estimate.total_bytes,
        "budget_bytes": budget,
        "available_bytes": snap["available"],
        "total_bytes": snap["total"],
    }
