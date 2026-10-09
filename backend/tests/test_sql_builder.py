import pytest

from app.sql_builder import build_sql


def make_parsed(**overrides):
    parsed = {"group_by": "canal", "where": [], "params": {}, "order": "DESC", "limit": 50}
    parsed.update(overrides)
    return parsed


def test_query_padrao():
    sql, params = build_sql(make_parsed())
    assert sql == (
        "SELECT canal, COUNT(*) AS total\n"
        "FROM logs\n"
        "WHERE 1=1\n"
        "GROUP BY canal\n"
        "ORDER BY total DESC\n"
        "LIMIT 50"
    )
    assert params == {}


def test_where_e_params():
    sql, params = build_sql(
        make_parsed(
            where=["severidade = :severidade", "LOWER(canal) = :canal"],
            params={"severidade": "alta", "canal": "globo"},
        )
    )
    assert "WHERE severidade = :severidade AND LOWER(canal) = :canal" in sql
    assert params == {"severidade": "alta", "canal": "globo"}
    assert "alta" not in sql
    assert "globo" not in sql


@pytest.mark.parametrize("group", ["canal", "equipamento", "tipo_erro"])
def test_group_by_permitido(group):
    sql, _ = build_sql(make_parsed(group_by=group))
    assert f"SELECT {group}, COUNT(*)" in sql
    assert f"GROUP BY {group}" in sql


def test_group_by_fora_da_whitelist_vira_canal():
    sql, _ = build_sql(make_parsed(group_by="id; DROP TABLE logs"))
    assert "GROUP BY canal" in sql
    assert "DROP" not in sql


def test_order_invalido_vira_desc():
    sql, _ = build_sql(make_parsed(order="DESC; DROP TABLE logs"))
    assert "ORDER BY total DESC\n" in sql
    assert "DROP" not in sql


@pytest.mark.parametrize("limit, expected", [(5, 5), (1000, 1000), (0, 50), (-1, 50), (1001, 50)])
def test_limit(limit, expected):
    sql, _ = build_sql(make_parsed(limit=limit))
    assert sql.endswith(f"LIMIT {expected}")
