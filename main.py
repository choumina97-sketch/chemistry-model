from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chemistry_service import MoleculeLookupError, build_molecule_card


app = FastAPI(title="Chemistry Teaching Flashcards")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


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
