import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.database import execute_query, ping
from app.nlp_parser import parse_question
from app.sql_builder import build_sql
from app.sql_validator import validate_sql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
audit_log = logging.getLogger("audit")
server_log = logging.getLogger("server")

from datetime import datetime
START_TIME = datetime.utcnow()

app = FastAPI(title="Text-to-SQL MVP")

# Em produção substitua pela origem real do frontend
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Query(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="Pergunta em linguagem natural sobre os logs",
        examples=["top canais com mais falhas nos últimos 7 dias"],
    )


@app.post("/query")
async def query(q: Query, request: Request):
    ts = datetime.now(timezone.utc).isoformat()
    ip = request.client.host if request.client else "unknown"

    try:
        parsed      = parse_question(q.question)
        sql, params = build_sql(parsed)
        safe_sql    = validate_sql(sql)
        data        = execute_query(safe_sql, params)

        audit_log.info(
            "QUERY_OK | ip=%s | input=%r | sql=%r | rows=%d | ts=%s",
            ip, q.question, safe_sql, len(data), ts,
        )

        return {
            "sql": safe_sql,
            "params": params,
            "rows": len(data),
            "data": data,
        }

    except ValueError as exc:
        audit_log.warning(
            "QUERY_BLOCKED | ip=%s | input=%r | reason=%s | ts=%s",
            ip, q.question, str(exc), ts,
        )
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        audit_log.error(
            "QUERY_ERROR | ip=%s | input=%r | error=%s | ts=%s",
            ip, q.question, str(exc), ts,
        )
        raise HTTPException(status_code=500, detail="Erro interno ao processar a consulta.")


@app.get("/health")
def health():
    try:
        return {"status": "ok", "db": ping()}
    except Exception as exc:
        server_log.error("HEALTH_DB_ERROR | error=%s", exc)
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")


@app.get("/metrics")
def metrics():
    """Retorna métricas simples de saúde/tempo de atividade."""
    uptime = datetime.utcnow() - START_TIME
    return {
        "status": "ok",
        "uptime_seconds": int(uptime.total_seconds()),
        "version": "0.1.0",
    }