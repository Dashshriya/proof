# PROOF

PROOF is an adaptive assessment chatbot for neurodivergent learners.

It does not simply grade the first answer. It keeps the learning objective fixed, identifies which concepts have or have not been demonstrated, and changes the route used to gather evidence.

## MVP

The prototype demonstrates:
- a learner-friendly chat interface
- a fixed learning objective
- adaptive follow-up questions
- concept/evidence tracking
- "I know it but I can't explain it" support
- a final evidence map
- optional LLM mode through the backend

## Run locally

### Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints, usually http://localhost:5173.

## Optional AI API

The MVP works in DEMO mode without an API key. To enable an OpenAI-compatible model, set:

```env
LLM_API_KEY=your_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=your_model
```

The backend keeps the assessment logic separate from the model call so the product does not depend on free-form chatbot answers alone.
