from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from chemistry_service import MoleculeLookupError, build_molecule_card
from issue_report_service import save_issue_report


app = FastAPI(title="Chemistry Teaching Flashcards")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class IssueReport(BaseModel):
    molecule_query: str = Field(default="", max_length=200)
    report_type: str = Field(default="general", max_length=80)
    message: str = Field(..., min_length=3, max_length=2000)
    contact: str = Field(default="", max_length=200)
    page_url: str = Field(default="", max_length=500)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "examples": ["glucose", "ethanol", "aspirin", "DDT", "vitamin c"],
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/molecule")
def molecule(name: str = Query(..., min_length=1, description="Molecule name")):
    try:
        return build_molecule_card(name)
    except MoleculeLookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/report")
async def report_issue(report: IssueReport, request: Request):
    try:
        save_result = save_issue_report(
            {
                **report.dict(),
                "user_agent": request.headers.get("user-agent", ""),
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not save the issue report.",
        ) from exc

    return {"status": "ok", **save_result}
