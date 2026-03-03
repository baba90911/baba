from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    raw_data: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class BuildResponse(BaseModel):
    message: str
    summary: dict[str, int]
    missing_filled: list[str]


class FaultRequest(BaseModel):
    element_type: str = Field(description="line|trafo|trafo3w|switch|gen|load")
    element_id: str
    reason: str = "manual"


class RecoveryRequest(BaseModel):
    event_id: str


class RealtimeUpdateRequest(BaseModel):
    loads: list[dict[str, Any]] = Field(default_factory=list)
    gens: list[dict[str, Any]] = Field(default_factory=list)


class TransferRequest(BaseModel):
    from_load_ids: list[str]
    to_bus_id: str
    ratio: float = Field(default=1.0, ge=0.0, le=1.0)


class SnapshotResponse(BaseModel):
    state_id: str
    ts: float
    note: str


class NMinusOneResponse(BaseModel):
    checked: int
    violations: list[dict[str, Any]]
