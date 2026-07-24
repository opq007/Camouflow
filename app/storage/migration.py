"""Profiles / proxies migration pack (ZIP import & export).

See `.omo/plans/profiles-proxies-migration-import-export.md` for the product spec.
"""

from __future__ import annotations

import io
import json
import logging
import re
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.storage.db import (
    db_add_account,
    db_get_accounts,
    db_get_setting,
    db_set_setting,
    db_update_account,
    profile_dir_for_email,
)

LOGGER = logging.getLogger(__name__)

SCHEMA_VERSION = 1
APP_NAME = "CamouFlow"

FINGERPRINT_FILES = (
    "camoufox_fingerprint.json",
    "cloakbrowser_fingerprint.json",
)

MANIFEST_NAME = "manifest.json"
ACCOUNTS_NAME = "accounts.json"
PROXY_POOLS_NAME = "proxy_pools.json"
FINGERPRINTS_DIR = "fingerprints"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_profile_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name or "profile")


def _csv_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _csv_join(names: Iterable[str]) -> str:
    return ", ".join(sorted({str(n).strip() for n in names if str(n).strip()}, key=str.lower))


def _load_proxy_pools() -> Dict[str, Any]:
    try:
        data = json.loads(db_get_setting("proxy_pools") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        LOGGER.exception("Failed to load proxy_pools for migration")
        return {}


def _save_proxy_pools(pools: Dict[str, Any]) -> None:
    db_set_setting("proxy_pools", json.dumps(pools, ensure_ascii=False))


def _account_name(acc: Dict[str, Any]) -> str:
    return str(acc.get("name") or acc.get("email") or "").strip()


def _stage_matches(acc: Dict[str, Any], stage: str) -> bool:
    """Match stage against comma-separated profile stages (same idea as list filter)."""
    wanted = str(stage or "").strip()
    if not wanted or wanted == "All tags":
        return True
    raw = str(acc.get("stage") or "")
    parts = [p.strip() for p in raw.split(",") if p.strip()] or ["No tag"]
    # Case-insensitive compare
    wanted_l = wanted.lower()
    return any(p.lower() == wanted_l for p in parts)


def _filter_accounts(
    accounts: Sequence[Dict[str, Any]],
    *,
    names: Optional[Sequence[str]] = None,
    stage: str = "",
) -> List[Dict[str, Any]]:
    selected = list(accounts)
    if stage:
        selected = [a for a in selected if _stage_matches(a, stage)]
    if names:
        wanted = {str(n).strip().lower() for n in names if str(n).strip()}
        selected = [a for a in selected if _account_name(a).lower() in wanted]
    return selected


def _referenced_pool_names(accounts: Sequence[Dict[str, Any]]) -> Set[str]:
    pools: Set[str] = set()
    for acc in accounts:
        pool = str(acc.get("proxy_pool") or "").strip()
        if pool:
            pools.add(pool)
    return pools


def _sanitize_pools_for_export(
    pools: Dict[str, Any],
    *,
    clear_assigned: bool,
    keep_profile_names: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Deep-copy pools; optionally clear or filter assigned_to."""
    out: Dict[str, Any] = {}
    keep_lower = {n.lower() for n in (keep_profile_names or set())}
    for pool_name, pool_data in pools.items():
        if not isinstance(pool_data, dict):
            continue
        proxies_in = pool_data.get("proxies") or []
        proxies_out: List[Dict[str, Any]] = []
        for px in proxies_in:
            if not isinstance(px, dict):
                continue
            item = deepcopy(px)
            if clear_assigned:
                item["assigned_to"] = ""
                item["status"] = "idle"
            elif keep_profile_names is not None:
                kept = [n for n in _csv_list(item.get("assigned_to")) if n.lower() in keep_lower]
                item["assigned_to"] = ", ".join(kept)
                item["status"] = "in use" if kept else "idle"
            proxies_out.append(item)
        out[str(pool_name)] = {
            "proxies": proxies_out,
            "created": str(pool_data.get("created") or ""),
        }
    return out


def _read_fingerprint_bytes(path: Path) -> Optional[bytes]:
    try:
        if not path.is_file():
            return None
        data = path.read_bytes()
        if not data:
            return None
        return data
    except Exception:
        LOGGER.exception("Failed to read fingerprint file %s", path)
        return None


def build_export_zip(
    *,
    scope: str,
    names: Optional[Sequence[str]] = None,
    stage: str = "",
    pool_names: Optional[Sequence[str]] = None,
) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Build a migration ZIP.

    Returns (zip_bytes, filename, manifest_dict).
    """
    scope_norm = str(scope or "").strip().lower()
    if scope_norm not in {"full", "profiles", "proxies"}:
        raise ValueError("scope must be full, profiles, or proxies")

    all_accounts = db_get_accounts()
    all_pools = _load_proxy_pools()
    warnings: List[str] = []

    export_accounts: List[Dict[str, Any]] = []
    export_pools: Dict[str, Any] = {}
    mode = scope_norm
    fingerprint_index: Dict[str, List[str]] = {}

    if scope_norm == "full":
        export_accounts = [deepcopy(a) for a in all_accounts]
        profile_names = {_account_name(a) for a in export_accounts if _account_name(a)}
        export_pools = _sanitize_pools_for_export(
            all_pools,
            clear_assigned=False,
            keep_profile_names=profile_names,
        )
        mode = "full"
    elif scope_norm == "proxies":
        if pool_names:
            wanted = {str(n).strip() for n in pool_names if str(n).strip()}
            selected = {k: v for k, v in all_pools.items() if k in wanted}
        else:
            selected = dict(all_pools)
        export_pools = _sanitize_pools_for_export(selected, clear_assigned=True)
        mode = "proxies"
    else:  # profiles
        filtered = _filter_accounts(all_accounts, names=names, stage=stage)
        export_accounts = [deepcopy(a) for a in filtered]
        if names and not stage and len(export_accounts) < len([n for n in (names or []) if str(n).strip()]):
            found = {_account_name(a).lower() for a in export_accounts}
            for n in names or []:
                if str(n).strip() and str(n).strip().lower() not in found:
                    warnings.append(f"profile not found: {n}")
        profile_names = {_account_name(a) for a in export_accounts if _account_name(a)}
        ref_pools = _referenced_pool_names(export_accounts)
        selected_pools = {k: v for k, v in all_pools.items() if k in ref_pools}
        missing_pools = sorted(ref_pools - set(selected_pools.keys()))
        for pool in missing_pools:
            warnings.append(f"referenced proxy pool missing: {pool}")
        export_pools = _sanitize_pools_for_export(
            selected_pools,
            clear_assigned=False,
            keep_profile_names=profile_names,
        )
        mode = "profiles_subset" if names else "profiles"

    # Collect fingerprints for exported profiles
    fingerprint_blobs: Dict[str, Dict[str, bytes]] = {}
    for acc in export_accounts:
        name = _account_name(acc)
        if not name:
            continue
        safe = _safe_profile_name(name)
        pdir = profile_dir_for_email(name)
        present: List[str] = []
        blobs: Dict[str, bytes] = {}
        for fname in FINGERPRINT_FILES:
            raw = _read_fingerprint_bytes(pdir / fname)
            if raw is None:
                # Distinguish missing vs read error only loosely
                if (pdir / fname).exists():
                    warnings.append(f"{name}: failed to read {fname}")
                continue
            blobs[fname] = raw
            present.append(fname)
        fingerprint_index[name] = present
        if blobs:
            fingerprint_blobs[safe] = blobs
        else:
            # No fingerprint files at all
            if pdir.exists():
                warnings.append(f"{name}: fingerprint file missing (will regenerate on first start)")
            else:
                warnings.append(f"{name}: profile directory missing; no fingerprints")

    manifest: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "app": APP_NAME,
        "exported_at": _utc_now_iso(),
        "mode": mode,
        "profiles": [_account_name(a) for a in export_accounts if _account_name(a)],
        "proxy_pools": list(export_pools.keys()),
        "fingerprints": fingerprint_index,
        "warnings": warnings,
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr(ACCOUNTS_NAME, json.dumps(export_accounts, ensure_ascii=False, indent=2))
        zf.writestr(PROXY_POOLS_NAME, json.dumps(export_pools, ensure_ascii=False, indent=2))
        for safe, blobs in fingerprint_blobs.items():
            for fname, data in blobs.items():
                zf.writestr(f"{FINGERPRINTS_DIR}/{safe}/{fname}", data)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"camouflow-migration-{stamp}.zip"
    return buf.getvalue(), filename, manifest


def _zip_read_json(zf: zipfile.ZipFile, name: str, default: Any) -> Any:
    try:
        with zf.open(name) as fh:
            raw = fh.read().decode("utf-8")
        return json.loads(raw)
    except KeyError:
        return default
    except Exception as exc:
        raise ValueError(f"Invalid JSON in {name}: {exc}") from exc


def _merge_proxy_pools(
    target: Dict[str, Any],
    incoming: Dict[str, Any],
    *,
    apply_assignments: bool,
    profile_names_written: Set[str],
) -> Dict[str, int]:
    """
    Merge incoming pools into target (in place).

    Returns counters: pools_created, pools_merged, proxies_added, proxies_deduped.
    """
    stats = {
        "pools_created": 0,
        "pools_merged": 0,
        "proxies_added": 0,
        "proxies_deduped": 0,
    }
    written_lower = {n.lower() for n in profile_names_written}

    for pool_name, pool_data in (incoming or {}).items():
        if not isinstance(pool_data, dict):
            continue
        name = str(pool_name)
        incoming_proxies = pool_data.get("proxies") or []
        if name not in target:
            # New pool: clone proxies with assignment policy
            new_proxies: List[Dict[str, Any]] = []
            for px in incoming_proxies:
                if not isinstance(px, dict):
                    continue
                item = deepcopy(px)
                if apply_assignments:
                    kept = [n for n in _csv_list(item.get("assigned_to")) if n.lower() in written_lower]
                    item["assigned_to"] = ", ".join(kept)
                    item["status"] = "in use" if kept else "idle"
                else:
                    item["assigned_to"] = ""
                    item["status"] = "idle"
                new_proxies.append(item)
            target[name] = {
                "proxies": new_proxies,
                "created": str(pool_data.get("created") or ""),
            }
            stats["pools_created"] += 1
            stats["proxies_added"] += len(new_proxies)
            continue

        # Existing pool: merge by value
        stats["pools_merged"] += 1
        existing = target[name]
        if not isinstance(existing, dict):
            existing = {"proxies": [], "created": ""}
            target[name] = existing
        proxies = list(existing.get("proxies") or [])
        by_value: Dict[str, int] = {}
        for idx, px in enumerate(proxies):
            if isinstance(px, dict):
                val = str(px.get("value") or "").strip()
                if val:
                    by_value[val] = idx

        for px in incoming_proxies:
            if not isinstance(px, dict):
                continue
            value = str(px.get("value") or "").strip()
            if not value:
                continue
            if value in by_value:
                stats["proxies_deduped"] += 1
                if apply_assignments:
                    # Optionally merge assignment for written profiles only
                    idx = by_value[value]
                    cur = proxies[idx]
                    if not isinstance(cur, dict):
                        continue
                    combined = set(_csv_list(cur.get("assigned_to")))
                    for n in _csv_list(px.get("assigned_to")):
                        if n.lower() in written_lower:
                            combined.add(n)
                    cur["assigned_to"] = ", ".join(sorted(combined, key=str.lower))
                    cur["status"] = "in use" if cur["assigned_to"] else "idle"
                continue

            item = deepcopy(px)
            if apply_assignments:
                kept = [n for n in _csv_list(item.get("assigned_to")) if n.lower() in written_lower]
                item["assigned_to"] = ", ".join(kept)
                item["status"] = "in use" if kept else "idle"
            else:
                item["assigned_to"] = ""
                item["status"] = "idle"
            if not item.get("name"):
                item["name"] = f"Proxy #{len(proxies) + 1}"
            proxies.append(item)
            by_value[value] = len(proxies) - 1
            stats["proxies_added"] += 1

        existing["proxies"] = proxies

    return stats


def import_migration_zip(
    zip_bytes: bytes,
    *,
    force_overwrite: bool = False,
) -> Dict[str, Any]:
    """
    Import a migration ZIP. Returns a result dict for the API.
    """
    if not zip_bytes:
        raise ValueError("Empty migration package")

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r")
    except zipfile.BadZipFile as exc:
        raise ValueError("Not a valid ZIP file") from exc

    with zf:
        # Basic zip-slip check
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in name.split("/"):
                raise ValueError(f"Unsafe path in archive: {info.filename}")

        manifest = _zip_read_json(zf, MANIFEST_NAME, None)
        if not isinstance(manifest, dict):
            raise ValueError("Missing or invalid manifest.json")
        if manifest.get("app") != APP_NAME:
            raise ValueError(f"Unsupported migration package app: {manifest.get('app')!r}")
        try:
            ver = int(manifest.get("schema_version"))
        except Exception as exc:
            raise ValueError("Invalid schema_version in manifest") from exc
        if ver != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {ver} (expected {SCHEMA_VERSION})")

        accounts_raw = _zip_read_json(zf, ACCOUNTS_NAME, [])
        if accounts_raw is None:
            accounts_raw = []
        if not isinstance(accounts_raw, list):
            raise ValueError("accounts.json must be a JSON array")

        pools_raw = _zip_read_json(zf, PROXY_POOLS_NAME, {})
        if pools_raw is None:
            pools_raw = {}
        if not isinstance(pools_raw, dict):
            raise ValueError("proxy_pools.json must be a JSON object")

        mode = str(manifest.get("mode") or "").strip().lower()
        apply_assignments = mode in {"full", "profiles", "profiles_subset"}

        # Index fingerprint members: fingerprints/{safe}/file
        fp_members: Dict[str, Dict[str, bytes]] = {}
        for info in zf.infolist():
            if info.is_dir():
                continue
            path = info.filename.replace("\\", "/")
            if not path.startswith(f"{FINGERPRINTS_DIR}/"):
                continue
            parts = path.split("/")
            if len(parts) != 3:
                continue
            _, safe, fname = parts
            if fname not in FINGERPRINT_FILES:
                continue
            try:
                fp_members.setdefault(safe, {})[fname] = zf.read(info)
            except Exception:
                LOGGER.exception("Failed to read fingerprint member %s", path)

    # --- Apply pools first (without profile-specific assignments until we know written names) ---
    # Two-phase: first import profiles to know which names are written, then merge pools with assignment filter.
    # But plan says pools → profiles → fingerprints. For assignment we need written names.
    # Practical approach:
    # 1. Merge pool structure with assignments cleared first OR merge after profiles.
    # We'll import profiles first into memory decisions, write profiles, then merge pools with apply_assignments.

    existing_accounts = db_get_accounts()
    existing_by_name: Dict[str, Dict[str, Any]] = {
        _account_name(a).lower(): a for a in existing_accounts if _account_name(a)
    }

    profiles_stats = {
        "added": 0,
        "skipped": 0,
        "overwritten": 0,
        "errors": [],
    }
    written_names: Set[str] = set()
    write_fingerprint_for: Set[str] = set()  # names that should receive fingerprint files

    for acc in accounts_raw:
        if not isinstance(acc, dict):
            profiles_stats["errors"].append("invalid account entry (not an object)")
            continue
        payload = deepcopy(acc)
        name = _account_name(payload)
        if not name:
            profiles_stats["errors"].append("account missing name")
            continue
        key = name.lower()
        try:
            if key in existing_by_name:
                if not force_overwrite:
                    profiles_stats["skipped"] += 1
                    continue
                # Overwrite: update all fields except keep identity via db_update_account
                updates = dict(payload)
                updates["name"] = name
                db_update_account(name, updates)
                profiles_stats["overwritten"] += 1
                written_names.add(name)
                write_fingerprint_for.add(name)
                existing_by_name[key] = payload
            else:
                # Ensure name field
                payload["name"] = name
                db_add_account(payload)
                profiles_stats["added"] += 1
                written_names.add(name)
                write_fingerprint_for.add(name)
                existing_by_name[key] = payload
        except Exception as exc:
            LOGGER.exception("Failed to import profile %s", name)
            profiles_stats["errors"].append(f"{name}: {exc}")

    # Merge proxy pools
    target_pools = _load_proxy_pools()
    proxy_stats = _merge_proxy_pools(
        target_pools,
        pools_raw,
        apply_assignments=apply_assignments and bool(written_names),
        profile_names_written=written_names,
    )
    _save_proxy_pools(target_pools)

    # Write fingerprints only for added/overwritten profiles
    fp_stats = {"written": 0, "skipped": 0}
    warnings: List[str] = list(manifest.get("warnings") or []) if isinstance(manifest.get("warnings"), list) else []

    for name in write_fingerprint_for:
        safe = _safe_profile_name(name)
        blobs = fp_members.get(safe) or {}
        if not blobs:
            fp_stats["skipped"] += 1
            continue
        pdir = profile_dir_for_email(name)
        try:
            pdir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            warnings.append(f"{name}: cannot create profile dir: {exc}")
            continue
        for fname, data in blobs.items():
            if fname not in FINGERPRINT_FILES:
                continue
            try:
                dest = pdir / fname
                # Atomic-ish write via temp replace
                tmp = dest.with_suffix(dest.suffix + ".tmp")
                tmp.write_bytes(data)
                tmp.replace(dest)
                fp_stats["written"] += 1
            except Exception as exc:
                LOGGER.exception("Failed to write fingerprint %s for %s", fname, name)
                warnings.append(f"{name}: failed to write {fname}: {exc}")

    # Profiles that were skipped should not get fingerprints (already handled)
    for name in [_account_name(a) for a in accounts_raw if isinstance(a, dict)]:
        if name and name not in write_fingerprint_for:
            # skipped profile — count fingerprint skip if package had files
            safe = _safe_profile_name(name)
            if safe in fp_members:
                fp_stats["skipped"] += 1

    result = {
        "ok": True,
        "profiles": profiles_stats,
        "proxies": proxy_stats,
        "fingerprints": fp_stats,
        "warnings": warnings,
        "mode": mode,
        "force_overwrite": bool(force_overwrite),
    }
    return result
