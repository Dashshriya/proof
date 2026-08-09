import os
import re
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="PROOF API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A small, transparent demo assessment. The learning objective stays fixed.
ASSESSMENT = {
    "title": "Why do seasons occur on Earth?",
    "objective": "Explain that Earth's axial tilt changes the angle and duration of sunlight received by each hemisphere during the year.",
    "concepts": [
        {"id": "tilt", "label": "Earth's axis is tilted", "keywords": ["tilt", "tilted", "axis"]},
        {"id": "angle", "label": "Sunlight angle changes", "keywords": ["angle", "direct", "directly", "slant"]},
        {"id": "hemisphere", "label": "The hemispheres receive different sunlight", "keywords": ["hemisphere", "north", "south", "different"]},
        {"id": "season", "label": "The tilt causes seasonal differences", "keywords": ["season", "summer", "winter", "seasons"]},
    ],
}

class StartRequest(BaseModel):
    assessment_id: str = "seasons"

class AnswerRequest(BaseModel):
    session_id: str
    answer: str
    mode: str = "text"

class Session(BaseModel):
    session_id: str
    objective: str
    concepts: List[Dict[str, Any]]
    demonstrated: List[str] = []
    history: List[Dict[str, Any]] = []
    step: int = 0

sessions: Dict[str, Session] = {}

def detect_concepts(answer: str) -> List[str]:
    text = answer.lower()
    hits = []
    for c in ASSESSMENT["concepts"]:
        if any(k in text for k in c["keywords"]):
            hits.append(c["id"])
    return hits

def next_missing(session: Session) -> Optional[Dict[str, Any]]:
    for c in session.concepts:
        if c["id"] not in session.demonstrated:
            return c
    return None

def fallback_question(concept: Dict[str, Any], step: int) -> Dict[str, str]:
    questions = {
        "tilt": (
            "Let’s start smaller. Is Earth’s axis tilted, or is it straight up relative to its orbit?",
            "choice",
        ),
        "angle": (
            "Imagine two rays of sunlight: one hits Earth more directly and one hits at a slant. Which one delivers more concentrated sunlight to a smaller area?",
            "choice",
        ),
        "hemisphere": (
            "When the Northern Hemisphere tilts toward the Sun, does it receive more direct sunlight than the Southern Hemisphere?",
            "choice",
        ),
        "season": (
            "So what is the connection between Earth’s tilt and the seasons?",
            "text",
        ),
    }
    q, mode = questions[concept["id"]]
    return {"text": q, "mode": mode}

def evidence(session: Session) -> List[Dict[str, Any]]:
    return [
        {
            "id": c["id"],
            "label": c["label"],
            "status": "demonstrated" if c["id"] in session.demonstrated else "not yet demonstrated",
        }
        for c in session.concepts
    ]

async def llm_question(session: Session, answer: str, missing: Dict[str, Any]) -> Optional[str]:
    key = os.getenv("LLM_API_KEY")
    base = os.getenv("LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("LLM_MODEL")
    if not (key and base and model):
        return None

    prompt = f"""
You are PROOF, an adaptive assessment engine.
Learning objective: {session.objective}
Concept still needing evidence: {missing['label']}
Student's latest response: {answer!r}
Previously demonstrated concepts: {session.demonstrated}

Write ONE short, supportive follow-up question that tests only the missing concept.
Do not reveal the answer. Do not lower the learning standard.
Return only the question.
""".strip()

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a careful adaptive assessment engine."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

@app.get("/api/assessment")
def get_assessment():
    return {
        "id": "seasons",
        "title": ASSESSMENT["title"],
        "objective": ASSESSMENT["objective"],
    }

@app.post("/api/start")
def start(req: StartRequest):
    import uuid
    sid = str(uuid.uuid4())
    session = Session(
        session_id=sid,
        objective=ASSESSMENT["objective"],
        concepts=ASSESSMENT["concepts"],
    )
    sessions[sid] = session
    first = fallback_question(ASSESSMENT["concepts"][0], 0)
    return {
        "session_id": sid,
        "message": "You don't need to write the full answer. We'll work out what you know step by step.",
        "question": first["text"],
        "mode": first["mode"],
        "evidence": evidence(session),
    }

@app.post("/api/answer")
async def answer(req: AnswerRequest):
    session = sessions.get(req.session_id)
    if not session:
        return {"error": "Session not found"}

    hits = detect_concepts(req.answer)
    newly = [h for h in hits if h not in session.demonstrated]
    session.demonstrated.extend(newly)
    session.history.append({"answer": req.answer, "mode": req.mode, "new_concepts": newly})
    session.step += 1

    missing = next_missing(session)

    if not missing:
        return {
            "complete": True,
            "reply": "You demonstrated the key ideas needed for this question. The original response format was not the only evidence of what you understood.",
            "evidence": evidence(session),
            "summary": "Understanding demonstrated across the core concepts.",
        }

    # If the student says they know it but cannot explain, move to a lower-expression-load probe.
    stuck = bool(re.search(r"\b(can't|cannot|dont|don't|unable|stuck|know it|know the answer)\b", req.answer.lower()))
    if stuck:
        reply = (
            "That’s okay. You don't have to produce the whole explanation at once. "
            "Let’s check one part of the idea."
        )
        q = fallback_question(missing, session.step)
    else:
        reply = "Good. I’m checking one specific part of the idea before we move on."
        llm_q = await llm_question(session, req.answer, missing)
        q = {"text": llm_q, "mode": "text"} if llm_q else fallback_question(missing, session.step)

    return {
        "complete": False,
        "reply": reply,
        "question": q["text"],
        "mode": q["mode"],
        "evidence": evidence(session),
        "newly_demonstrated": newly,
    }

@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return {"evidence": evidence(session), "history": session.history}
