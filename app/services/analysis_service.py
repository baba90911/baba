from __future__ import annotations

import copy
from typing import Any

import pandapower as pp

from app.services.state_manager import GridStateManager


class AnalysisService:
    def __init__(self, manager: GridStateManager) -> None:
        self.manager = manager

    def update_realtime(self, loads: list[dict[str, Any]], gens: list[dict[str, Any]]) -> None:
        net = self.manager.net
        if net is None:
            raise ValueError("network is not initialized")

        for upd in loads:
            ext_id = str(upd["id"])
            idx = self.manager.lookup["load"].get(ext_id)
            if idx is None:
                continue
            if "p_mw" in upd:
                net.load.at[idx, "p_mw"] = float(upd["p_mw"])
            if "q_mvar" in upd:
                net.load.at[idx, "q_mvar"] = float(upd["q_mvar"])

        for upd in gens:
            ext_id = str(upd["id"])
            idx = self.manager.lookup["gen"].get(ext_id)
            if idx is None:
                continue
            if "p_mw" in upd:
                net.gen.at[idx, "p_mw"] = float(upd["p_mw"])

    def n_minus_one_scan(self) -> dict[str, Any]:
        net = self.manager.net
        if net is None:
            raise ValueError("network is not initialized")

        violations: list[dict[str, Any]] = []
        checked = 0

        for table in ("line", "trafo"):
            for idx in getattr(net, table).index:
                if not getattr(net, table).at[idx, "in_service"]:
                    continue
                checked += 1
                test_net = copy.deepcopy(net)
                getattr(test_net, table).at[idx, "in_service"] = False
                try:
                    pp.runpp(test_net, calculate_voltage_angles=True, init="auto")
                except Exception as exc:  # noqa: BLE001
                    violations.append({"type": table, "idx": int(idx), "issue": f"not converged: {exc}"})
                    continue

                overload_lines = (
                    test_net.res_line[test_net.res_line.loading_percent > 100.0].index.tolist()
                    if len(test_net.line.index)
                    else []
                )
                over_vm = test_net.res_bus[(test_net.res_bus.vm_pu > 1.1) | (test_net.res_bus.vm_pu < 0.9)].index.tolist()
                if overload_lines or over_vm:
                    violations.append(
                        {
                            "type": table,
                            "idx": int(idx),
                            "overload_lines": overload_lines,
                            "voltage_violations": over_vm,
                        }
                    )

        return {"checked": checked, "violations": violations}

    def transfer_load(self, from_load_ids: list[str], to_bus_id: str, ratio: float) -> dict[str, Any]:
        net = self.manager.net
        if net is None:
            raise ValueError("network is not initialized")

        to_bus_idx = self.manager.lookup.get("bus", {}).get(to_bus_id)
        if to_bus_idx is None:
            to_bus_idx = next((k for ext, k in self.manager.lookup.get("bus", {}).items() if ext == to_bus_id), None)
        if to_bus_idx is None:
            raise KeyError(f"target bus {to_bus_id} not found")

        moved = []
        for ext_id in from_load_ids:
            idx = self.manager.lookup["load"].get(ext_id)
            if idx is None:
                continue
            origin_bus = int(net.load.at[idx, "bus"])
            new_p = float(net.load.at[idx, "p_mw"]) * (1 - ratio)
            new_q = float(net.load.at[idx, "q_mvar"]) * (1 - ratio)
            transferred_p = float(net.load.at[idx, "p_mw"]) - new_p
            transferred_q = float(net.load.at[idx, "q_mvar"]) - new_q
            net.load.at[idx, "p_mw"] = new_p
            net.load.at[idx, "q_mvar"] = new_q
            pp.create_load(net, bus=to_bus_idx, p_mw=transferred_p, q_mvar=transferred_q, name=f"transfer_from_{ext_id}")
            moved.append({"load_id": ext_id, "from_bus": origin_bus, "to_bus": to_bus_idx})

        self.manager.transfer_log.append({"to_bus": to_bus_id, "moved": moved, "ratio": ratio})
        return {"moved": moved, "ratio": ratio}

    def simple_predict(self, horizon_steps: int = 4) -> dict[str, Any]:
        net = self.manager.net
        if net is None:
            raise ValueError("network is not initialized")

        base_load = float(net.load.p_mw.sum()) if len(net.load.index) else 0.0
        base_gen = float(net.gen.p_mw.sum()) if len(net.gen.index) else 0.0
        forecasts = []
        for step in range(1, horizon_steps + 1):
            growth = 1 + 0.015 * step
            forecasts.append(
                {
                    "step": step,
                    "pred_load_mw": round(base_load * growth, 3),
                    "pred_gen_mw": round(base_gen * (1 + 0.01 * step), 3),
                }
            )
        return {"horizon_steps": horizon_steps, "forecast": forecasts}
