from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import pandapower as pp


@dataclass
class FaultEvent:
    event_id: str
    element_type: str
    element_id: str
    table_index: int
    previous_state: bool
    timestamp: float = field(default_factory=time.time)


class GridStateManager:
    def __init__(self) -> None:
        self.net: pp.pandapowerNet | None = None
        self.lookup: dict[str, dict[str, int]] = {}
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.faults: dict[str, FaultEvent] = {}
        self.transfer_log: list[dict[str, Any]] = []

    def set_network(self, net: pp.pandapowerNet, lookup: dict[str, dict[str, int]]) -> None:
        self.net = net
        self.lookup = lookup
        self.snapshots.clear()
        self.faults.clear()
        self.transfer_log.clear()

    def save_snapshot(self, note: str) -> tuple[str, float]:
        if self.net is None:
            raise ValueError("network is not initialized")
        sid = str(uuid.uuid4())
        ts = time.time()
        self.snapshots[sid] = {"net": copy.deepcopy(self.net), "ts": ts, "note": note}
        return sid, ts

    def restore_snapshot(self, snapshot_id: str) -> None:
        shot = self.snapshots.get(snapshot_id)
        if not shot:
            raise KeyError(f"snapshot {snapshot_id} not found")
        self.net = copy.deepcopy(shot["net"])

    def apply_fault(self, element_type: str, element_id: str, reason: str = "manual") -> str:
        if self.net is None:
            raise ValueError("network is not initialized")
        mapping = {
            "line": "line",
            "trafo": "trafo",
            "trafo3w": "trafo3w",
            "gen": "gen",
            "load": "load",
        }
        if element_type == "switch":
            idx = self.lookup["switch"][element_id]
            prev = bool(self.net.switch.at[idx, "closed"])
            self.net.switch.at[idx, "closed"] = False
        else:
            table = mapping[element_type]
            idx = self.lookup[table][element_id]
            prev = bool(getattr(self.net, table).at[idx, "in_service"])
            getattr(self.net, table).at[idx, "in_service"] = False

        event_id = str(uuid.uuid4())
        self.faults[event_id] = FaultEvent(
            event_id=event_id,
            element_type=element_type,
            element_id=element_id,
            table_index=idx,
            previous_state=prev,
        )
        return event_id

    def recover_fault(self, event_id: str) -> None:
        if self.net is None:
            raise ValueError("network is not initialized")
        event = self.faults.get(event_id)
        if not event:
            raise KeyError(f"fault event {event_id} not found")

        if event.element_type == "switch":
            self.net.switch.at[event.table_index, "closed"] = event.previous_state
        else:
            table = event.element_type
            getattr(self.net, table).at[event.table_index, "in_service"] = event.previous_state

    def power_flow(self) -> dict[str, Any]:
        if self.net is None:
            raise ValueError("network is not initialized")
        pp.runpp(self.net, calculate_voltage_angles=True, init="auto")
        return {
            "converged": bool(self.net.converged),
            "bus_vm_pu": self.net.res_bus.vm_pu.round(4).to_dict(),
            "line_loading_percent": self.net.res_line.loading_percent.round(2).fillna(0).to_dict()
            if len(self.net.line.index)
            else {},
        }
