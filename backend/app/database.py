import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "text_to_sql_mvp")
DB_PORT     = os.getenv("DB_PORT", "3306")

# usar driver mariadb; a string de conexão usa o dialect+driver
DATABASE_URL = (
    f"mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

logger = logging.getLogger(__name__)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"charset": "utf8mb4"},
    future=True,
)


@event.listens_for(engine, "connect")
def set_session_options(dbapi_conn, _):
    try:
        with dbapi_conn.cursor() as cur:
            cur.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'")
            cur.execute("SET time_zone = '+00:00'")
    except Exception as exc:
        logger.exception("Erro ao configurar sessão DB: %s", exc)


def execute_query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute query parametrizada e retorne lista de dicionários.

    Em caso de erro de banco, lança a mesma exceção para o caller tratá-la.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = list(result.keys())
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except Exception:
        logger.exception("Erro ao executar query: %s — params=%r", sql, params)
        raise