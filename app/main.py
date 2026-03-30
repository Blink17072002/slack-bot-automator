from fastapi import FastAPI, Request, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import engine, Base, get_db
from app.config import CRON_HOUR, CRON_MINUTE
from app.pipeline import execute_daily_pipeline
from app.models import Source, PipelineRun


log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("system.log", encoding="utf-8"),
    ]
)

Base.metadata.create_all(bind=engine)
scheduler = BackgroundScheduler()


def run_pipeline():
    """Triggered by the scheduler to run the ETL pipeline."""
    try:
        execute_daily_pipeline()
    except Exception as e:
        logging.error(f"Scheduler failed to run pipeline: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        run_pipeline,
        trigger=CronTrigger(hour=CRON_HOUR, minute=CRON_MINUTE),
        id="news_pipeline_job",  
        replace_existing=True
    )
    scheduler.start()
    logging.info(f"Scheduler started. Pipeline will run daily at {CRON_HOUR:02d}:{CRON_MINUTE:02d}")
    yield
    scheduler.shutdown()
    logging.info("Scheduler shut down.")

app = FastAPI(title="News Digest Bot Admin", lifespan=lifespan)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.id.desc()).all()
    runs = db.query(PipelineRun).order_by(PipelineRun.id.desc()).limit(10).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "sources": sources, "runs": runs}
    )


@app.post("/sources")
async def add_source(name: str=Form(...), url: str=Form(...), source_type: str=Form(...), db: Session=Depends(get_db)):
    new_source = Source(name=name, url=url, source_type=source_type)
    db.add(new_source)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to add source: {e}")
    return RedirectResponse(url="/", status_code=303)


@app.post("/sources/{source_id}/delete")
async def delete_source(source_id: int, db: Session=Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if source:
        db.delete(source)
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/trigger_run")
async def trigger_run(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_pipeline)
    return RedirectResponse(url="/", status_code=303)