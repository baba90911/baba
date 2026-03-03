from __future__ import annotations

from typing import Any


REQUIRED_KEYS = {
    "BUSBAR",
    "ACLINE",
    "TRANSFORMER",
    "TRANSFORMER3",
    "GEN",
    "STATISTIC_GEN",
    "LOAD",
    "KG",
}


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return s
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            return s
    return value


def normalize_payload(payload: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    normalized: dict[str, list[dict[str, Any]]] = {}
    for key, records in payload.items():
        normalized[key] = [{k: normalize_value(v) for k, v in row.items()} for row in records]
    return normalized


def fill_missing_elements(payload: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    missing: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in payload:
            payload[key] = []
            missing.append(key)

    if not payload["BUSBAR"]:
        payload["BUSBAR"].append(
            {
                "id": "AUTO_BUS_110KV",
                "name": "Auto 110kV Bus",
                "vn_kv": 110,
                "type": "b",
                "min_vm_pu": 0.9,
                "max_vm_pu": 1.1,
            }
        )
        missing.append("BUSBAR:default_bus")

    return payload, missing
