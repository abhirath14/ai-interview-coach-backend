import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS, GROQ_API_KEY, MODEL_NAME
from app.interviewer import get_next_message
from app.report import generate_report
from app.schemas import (
    AnswerRequest,
    InterviewerReply,
    Message,
    Report,
    ReportRequest,
    StartRequest,
)

logger = logging.getLogger("ai_interview_coach")

PLACEHOLDER_KEY = "your_groq_api_key_here"
AI_SERVICE_ERROR = "Failed to reach the AI service. Please try again."


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("AI Interview Coach API")
    print(f"Model: {MODEL_NAME}")
    print(f"Allowed origins: {', '.join(ALLOWED_ORIGINS)}")
    if not GROQ_API_KEY or GROQ_API_KEY == PLACEHOLDER_KEY:
        print("WARNING: GROQ_API_KEY is not set. Add a real key to backend/.env")
    else:
        print("GROQ_API_KEY loaded.")
    print("=" * 60)
    yield


app = FastAPI(title="AI Interview Coach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"] if part != "body")
    message = first_error["msg"]
    detail = f"{field}: {message}" if field else message
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


@app.get("/")
def read_root():
    return {"message": "AI Interview Coach API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/interview/start", response_model=InterviewerReply)
def start_interview(request: StartRequest):
    try:
        return get_next_message(request.topic, request.difficulty, [])
    except Exception:
        logger.exception("Interviewer call failed on /interview/start")
        raise HTTPException(status_code=502, detail=AI_SERVICE_ERROR)


@app.post("/interview/answer", response_model=InterviewerReply)
def submit_answer(request: AnswerRequest):
    history = request.history + [Message(role="candidate", content=request.answer)]
    try:
        return get_next_message(request.topic, request.difficulty, history)
    except Exception:
        logger.exception("Interviewer call failed on /interview/answer")
        raise HTTPException(status_code=502, detail=AI_SERVICE_ERROR)


@app.post("/interview/report", response_model=Report)
def get_report(request: ReportRequest):
    try:
        return generate_report(request.topic, request.difficulty, request.history)
    except Exception:
        logger.exception("Report generation failed on /interview/report")
        raise HTTPException(status_code=502, detail=AI_SERVICE_ERROR)
