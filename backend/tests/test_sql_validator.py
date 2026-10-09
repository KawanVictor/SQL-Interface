import pytest

from app.nlp_parser import parse_question
from app.sql_builder import build_sql
from app.sql_validator import validate_sql


def test_select_valido_passa_e_volta_sem_espacos_nas_pontas():
    assert validate_sql("  SELECT canal FROM logs  ") == "SELECT canal FROM logs"


@pytest.mark.parametrize(
    "question",
    [
        "top 5 canais com mais falhas nos últimos 7 dias",
        "equipamentos com mais erros críticos hoje",
        "tipos de erro da Globo no rewrapper-01",
    ],
)
def test_sql_gerado_pelo_builder_passa(question):
    sql, _ = build_sql(parse_question(question))
    assert validate_sql(sql) == sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM logs",
        "UPDATE logs SET canal = 'x'",
        "SHOW TABLES",
    ],
)
def test_somente_select(sql):
    with pytest.raises(ValueError, match="Somente consultas SELECT"):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM logs; DROP TABLE logs",
        "SELECT * FROM logs -- comentario",
        "SELECT * FROM logs /* comentario */",
        "SELECT SLEEP(10) FROM logs",
        "SELECT * FROM logs INTO OUTFILE '/tmp/x'",
        "SELECT LOAD_FILE('/etc/passwd') FROM logs",
    ],
)
def test_padroes_bloqueados(sql):
    with pytest.raises(ValueError, match="Padrão não permitido"):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM usuarios",
        "SELECT * FROM logs JOIN usuarios ON 1=1",
    ],
)
def test_tabela_nao_autorizada(sql):
    with pytest.raises(ValueError, match="Tabela não autorizada"):
        validate_sql(sql)
