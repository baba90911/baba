from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.data_adapter import fill_missing_elements, normalize_payload
from app.core.grid_builder import GridBuilder
from app.models.schemas import (
    BuildRequest,
    BuildResponse,
    FaultRequest,
    NMinusOneResponse,
    RealtimeUpdateRequest,
    RecoveryRequest,
    SnapshotResponse,
    TransferRequest,
)
from app.services.analysis_service import AnalysisService
from app.services.state_manager import GridStateManager

router = APIRouter(prefix="/api/v1")
manager = GridStateManager()
analysis = AnalysisService(manager)


@router.post("/grid/build", response_model=BuildResponse)
def build_grid(req: BuildRequest) -> BuildResponse:
    payload = normalize_payload(req.raw_data)
    payload, missing = fill_missing_elements(payload)

    builder = GridBuilder()
    net = builder.build(payload)
    manager.set_network(net, builder.element_lookup)
    sid, _ = manager.save_snapshot("post-build")
    return BuildResponse(
        message="grid built",
        summary={k: len(v) for k, v in payload.items()},
        missing_filled=missing + [f"snapshot:{sid}"],
    )


@router.get("/grid/state")
def get_state() -> dict:
    try:
        return manager.power_flow()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/fault")
def simulate_fault(req: FaultRequest) -> dict:
    try:
        event_id = manager.apply_fault(req.element_type, req.element_id, req.reason)
        return {"event_id": event_id, "status": "fault_applied"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/recover")
def recover_fault(req: RecoveryRequest) -> dict:
    try:
        manager.recover_fault(req.event_id)
        return {"status": "recovered", "event_id": req.event_id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/grid/nminus1", response_model=NMinusOneResponse)
def n_minus_one() -> NMinusOneResponse:
    try:
        result = analysis.n_minus_one_scan()
        return NMinusOneResponse(**result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/realtime")
def realtime_update(req: RealtimeUpdateRequest) -> dict:
    try:
        analysis.update_realtime(req.loads, req.gens)
        return {"status": "updated"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/transfer")
def transfer(req: TransferRequest) -> dict:
    try:
        return analysis.transfer_load(req.from_load_ids, req.to_bus_id, req.ratio)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/snapshot", response_model=SnapshotResponse)
def create_snapshot(note: str = "manual") -> SnapshotResponse:
    try:
        sid, ts = manager.save_snapshot(note)
        return SnapshotResponse(state_id=sid, ts=ts, note=note)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/grid/restore")
def restore(snapshot_id: str) -> dict:
    try:
        manager.restore_snapshot(snapshot_id)
        return {"status": "restored", "snapshot_id": snapshot_id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/grid/predict")
def predict(horizon_steps: int = 4) -> dict:
    try:
        return analysis.simple_predict(horizon_steps)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
