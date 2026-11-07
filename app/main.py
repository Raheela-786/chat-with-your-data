from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import answer_question
from app.charts import build_chart

app = FastAPI(title="Chat With Your Data")
app.mount("/static", StaticFiles(directory="static"), name="static")


class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: Question):
    result = answer_question(body.question)
    chart = build_chart(result["columns"], result["rows"]) if result["ok"] else None
    return {
        "ok": result["ok"],
        "sql": result["sql"],
        "columns": result["columns"],
        "rows": result["rows"],
        "attempts": result["attempts"],
        "message": result.get("message"),
        "chart": chart,
    }