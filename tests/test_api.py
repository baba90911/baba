from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_build_and_state() -> None:
    payload = {
        "raw_data": {
            "BUSBAR": [
                {"id": "B1", "name": "Bus1", "vn_kv": "110", "min_vm_pu": "0.9", "max_vm_pu": "1.1"},
                {"id": "B2", "name": "Bus2", "vn_kv": "110", "min_vm_pu": "0.9", "max_vm_pu": "1.1"},
            ],
            "ACLINE": [
                {
                    "id": "L1",
                    "from_bus": "B1",
                    "to_bus": "B2",
                    "length_km": "10",
                    "r_ohm_per_km": "0.05",
                    "x_ohm_per_km": "0.2",
                    "c_nf_per_km": "10",
                    "max_i_ka": "1.0",
                    "state": "运行",
                }
            ],
            "LOAD": [{"id": "LD1", "bus": "B2", "p_mw": "20", "q_mvar": "5"}],
            "GEN": [{"id": "G1", "bus": "B1", "p_mw": "25", "p_min": "0", "p_max": "40"}],
        }
    }
    r = client.post("/api/v1/grid/build", json=payload)
    assert r.status_code == 200

    s = client.get("/api/v1/grid/state")
    assert s.status_code == 200
    assert s.json()["converged"] is True


def test_nminus1_endpoint() -> None:
    r = client.get("/api/v1/grid/nminus1")
    assert r.status_code == 200
    assert "checked" in r.json()
