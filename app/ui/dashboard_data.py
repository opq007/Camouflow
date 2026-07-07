"""Small data helpers for dashboard-like UI summaries."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping


def proxy_pool_stats(proxy_pools: Mapping[str, Mapping[str, Any]]) -> Dict[str, int]:
    total = 0
    assigned = 0
    healthy = 0
    for pool in proxy_pools.values():
        proxies = pool.get("proxies", []) if isinstance(pool, Mapping) else []
        if not isinstance(proxies, list):
            continue
        total += len(proxies)
        for proxy in proxies:
            if not isinstance(proxy, Mapping):
                continue
            if proxy.get("assigned_to"):
                assigned += 1
            last_check = proxy.get("last_check")
            if isinstance(last_check, Mapping) and last_check.get("status") == "ok":
                healthy += 1
    return {
        "pools": len(proxy_pools),
        "total": total,
        "assigned": assigned,
        "healthy": healthy,
    }


def build_dashboard_metrics(
    accounts: Iterable[Mapping[str, Any]],
    proxy_pools: Mapping[str, Mapping[str, Any]],
    live_browsers: Mapping[str, Any] | None = None,
    maybe_live_browsers: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    if maybe_live_browsers is not None:
        proxy_pools, live_browsers = live_browsers or {}, maybe_live_browsers
    live_browsers = live_browsers or {}
    account_list = list(accounts)
    proxy_stats = proxy_pool_stats(proxy_pools)
    stages = Counter(str(account.get("stage") or "Undefined") for account in account_list)
    return {
        "profiles": len(account_list),
        "running": len(live_browsers),
        "proxy_total": proxy_stats["total"],
        "proxy_healthy": proxy_stats["healthy"],
        "proxy_assigned": proxy_stats["assigned"],
        "proxy_pools": proxy_stats["pools"],
        "stages": dict(stages),
    }


def recent_log_lines(text: str, limit: int = 5) -> List[str]:
    if limit <= 0:
        return []
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return lines[-limit:]
