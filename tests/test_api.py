import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app import app

client = TestClient(app)


def test_start_returns_a_session_and_first_question():
    response = client.post("/api/start", json={"assessment_id": "seasons"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["question"]
    assert len(payload["evidence"]) == 4


def test_unknown_session_returns_not_found():
    response = client.post(
        "/api/answer",
        json={"session_id": "missing-session", "answer": "I am not sure."},
    )

    assert response.status_code == 404


def test_answer_can_complete_the_fixed_objective():
    started = client.post("/api/start", json={"assessment_id": "seasons"}).json()
    response = client.post(
        "/api/answer",
        json={
            "session_id": started["session_id"],
            "answer": (
                "Earth's axis is tilted. The angle of direct sunlight changes. "
                "The north and south hemispheres receive different sunlight, "
                "which causes summer and winter seasons."
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["complete"] is True


def test_empty_answer_is_rejected():
    started = client.post("/api/start", json={"assessment_id": "seasons"}).json()
    response = client.post(
        "/api/answer",
        json={"session_id": started["session_id"], "answer": ""},
    )

    assert response.status_code == 422
