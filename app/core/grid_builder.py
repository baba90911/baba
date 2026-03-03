from __future__ import annotations

from typing import Any

import pandapower as pp


class GridBuilder:
    def __init__(self) -> None:
        self.bus_lookup: dict[str, int] = {}
        self.element_lookup: dict[str, dict[str, int]] = {
            "bus": self.bus_lookup,
            "line": {},
            "trafo": {},
            "trafo3w": {},
            "switch": {},
            "gen": {},
            "sgen": {},
            "load": {},
        }

    def build(self, payload: dict[str, list[dict[str, Any]]]) -> pp.pandapowerNet:
        net = pp.create_empty_network(sn_mva=100.0, f_hz=50)
        self._create_buses(net, payload.get("BUSBAR", []))
        self._create_lines(net, payload.get("ACLINE", []))
        self._create_transformers(net, payload.get("TRANSFORMER", []))
        self._create_transformers3w(net, payload.get("TRANSFORMER3", []))
        self._create_generators(net, payload.get("GEN", []), payload.get("STATISTIC_GEN", []))
        self._create_loads(net, payload.get("LOAD", []))
        self._create_switches(net, payload.get("KG", []))
        return net

    def _bus_idx(self, net: pp.pandapowerNet, ext_id: str, fallback_name: str) -> int:
        if ext_id in self.bus_lookup:
            return self.bus_lookup[ext_id]
        idx = pp.create_bus(net, vn_kv=110.0, name=fallback_name, min_vm_pu=0.9, max_vm_pu=1.1)
        self.bus_lookup[ext_id] = idx
        return idx

    def _create_buses(self, net: pp.pandapowerNet, buses: list[dict[str, Any]]) -> None:
        for b in buses:
            ext_id = str(b.get("id"))
            idx = pp.create_bus(
                net,
                vn_kv=float(b.get("vn_kv", 110.0)),
                name=str(b.get("name", ext_id)),
                type=str(b.get("type", "b")),
                min_vm_pu=float(b.get("min_vm_pu", 0.9)),
                max_vm_pu=float(b.get("max_vm_pu", 1.1)),
            )
            self.bus_lookup[ext_id] = idx

    def _create_lines(self, net: pp.pandapowerNet, lines: list[dict[str, Any]]) -> None:
        for line in lines:
            ext_id = str(line.get("id"))
            from_bus = self._bus_idx(net, str(line.get("from_bus")), f"AUTO_{line.get('from_bus')}")
            to_bus = self._bus_idx(net, str(line.get("to_bus")), f"AUTO_{line.get('to_bus')}")
            idx = pp.create_line_from_parameters(
                net,
                from_bus=from_bus,
                to_bus=to_bus,
                length_km=float(line.get("length_km", 1.0)),
                r_ohm_per_km=float(line.get("r_ohm_per_km", 0.03)),
                x_ohm_per_km=float(line.get("x_ohm_per_km", 0.3)),
                c_nf_per_km=float(line.get("c_nf_per_km", 10.0)),
                max_i_ka=float(line.get("max_i_ka", 1.0)),
                name=str(line.get("name", ext_id)),
                in_service=str(line.get("state", "运行")) == "运行",
            )
            self.element_lookup["line"][ext_id] = idx

    def _create_transformers(self, net: pp.pandapowerNet, trafos: list[dict[str, Any]]) -> None:
        for tr in trafos:
            ext_id = str(tr.get("id"))
            hv_bus = self._bus_idx(net, str(tr.get("hv_bus")), f"AUTO_{tr.get('hv_bus')}")
            lv_bus = self._bus_idx(net, str(tr.get("lv_bus")), f"AUTO_{tr.get('lv_bus')}")
            idx = pp.create_transformer_from_parameters(
                net,
                hv_bus=hv_bus,
                lv_bus=lv_bus,
                sn_mva=float(tr.get("sn_mva", 100.0)),
                vn_hv_kv=float(tr.get("vn_hv_kv", 220.0)),
                vn_lv_kv=float(tr.get("vn_lv_kv", 110.0)),
                vk_percent=float(tr.get("vk_percent", 12.0)),
                vkr_percent=float(tr.get("vkr_percent", 0.3)),
                pfe_kw=float(tr.get("pfe_kw", 20.0)),
                i0_percent=float(tr.get("i0_percent", 0.1)),
                shift_degree=float(tr.get("shift_degree", 0.0)),
                name=str(tr.get("name", ext_id)),
            )
            self.element_lookup["trafo"][ext_id] = idx

    def _create_transformers3w(self, net: pp.pandapowerNet, trafos: list[dict[str, Any]]) -> None:
        for tr in trafos:
            ext_id = str(tr.get("id"))
            hv_bus = self._bus_idx(net, str(tr.get("hv_bus")), f"AUTO_{tr.get('hv_bus')}")
            mv_bus = self._bus_idx(net, str(tr.get("mv_bus")), f"AUTO_{tr.get('mv_bus')}")
            lv_bus = self._bus_idx(net, str(tr.get("lv_bus")), f"AUTO_{tr.get('lv_bus')}")
            idx = pp.create_transformer3w_from_parameters(
                net,
                hv_bus=hv_bus,
                mv_bus=mv_bus,
                lv_bus=lv_bus,
                sn_hv_mva=float(tr.get("sn_hv_mva", tr.get("sn_mva", 300.0))),
                sn_mv_mva=float(tr.get("sn_mv_mva", tr.get("sn_mva", 300.0))),
                sn_lv_mva=float(tr.get("sn_lv_mva", tr.get("sn_mva", 300.0))),
                vn_hv_kv=float(tr.get("vn_hv_kv", 500.0)),
                vn_mv_kv=float(tr.get("vn_mv_kv", 220.0)),
                vn_lv_kv=float(tr.get("vn_lv_kv", 35.0)),
                vk_hv_percent=float(tr.get("vk_percent", 12.0)),
                vk_mv_percent=float(tr.get("vk_percent", 12.0)),
                vk_lv_percent=float(tr.get("vk_percent", 12.0)),
                vkr_hv_percent=float(tr.get("vkr_percent", 0.3)),
                vkr_mv_percent=float(tr.get("vkr_percent", 0.3)),
                vkr_lv_percent=float(tr.get("vkr_percent", 0.3)),
                pfe_kw=float(tr.get("pfe_kw", 20.0)),
                i0_percent=float(tr.get("i0_percent", 0.1)),
                shift_mv_degree=float(tr.get("shift_degree", 0.0)),
                shift_lv_degree=float(tr.get("shift_degree", 0.0)),
                name=str(tr.get("name", ext_id)),
            )
            self.element_lookup["trafo3w"][ext_id] = idx

    def _create_generators(self, net: pp.pandapowerNet, gens: list[dict[str, Any]], statics: list[dict[str, Any]]) -> None:
        for g in gens:
            ext_id = str(g.get("id"))
            bus = self._bus_idx(net, str(g.get("bus")), f"AUTO_{g.get('bus')}")
            idx = pp.create_gen(
                net,
                bus=bus,
                p_mw=float(g.get("p_mw", 0.0)),
                vm_pu=1.0,
                min_p_mw=float(g.get("p_min", 0.0)),
                max_p_mw=float(g.get("p_max", 1000.0)),
                name=str(g.get("name", ext_id)),
            )
            self.element_lookup["gen"][ext_id] = idx

        for sg in statics:
            ext_id = str(sg.get("id"))
            bus = self._bus_idx(net, str(sg.get("bus")), f"AUTO_{sg.get('bus')}")
            idx = pp.create_sgen(
                net,
                bus=bus,
                p_mw=float(sg.get("p_mw", 0.0)),
                q_mvar=float(sg.get("q_mvar", 0.0)),
                name=str(sg.get("name", ext_id)),
            )
            self.element_lookup["sgen"][ext_id] = idx

    def _create_loads(self, net: pp.pandapowerNet, loads: list[dict[str, Any]]) -> None:
        for ld in loads:
            ext_id = str(ld.get("id"))
            bus = self._bus_idx(net, str(ld.get("bus")), f"AUTO_{ld.get('bus')}")
            idx = pp.create_load(
                net,
                bus=bus,
                p_mw=float(ld.get("p_mw", 0.0)),
                q_mvar=float(ld.get("q_mvar", 0.0)),
                name=str(ld.get("name", ext_id)),
            )
            self.element_lookup["load"][ext_id] = idx

    def _create_switches(self, net: pp.pandapowerNet, switches: list[dict[str, Any]]) -> None:
        for sw in switches:
            ext_id = str(sw.get("id"))
            bus = self._bus_idx(net, str(sw.get("bus")), f"AUTO_{sw.get('bus')}")
            target_ext = str(sw.get("element"))
            target_idx = self.bus_lookup.get(target_ext, bus)
            idx = pp.create_switch(
                net,
                bus=bus,
                element=target_idx,
                et=str(sw.get("et", "b")),
                closed=str(sw.get("closed", "1")) == "1",
                type="CB",
                name=str(sw.get("name", ext_id)),
            )
            self.element_lookup["switch"][ext_id] = idx
