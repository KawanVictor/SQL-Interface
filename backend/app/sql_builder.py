def build_sql(parsed: dict) -> tuple[str, dict]:
    """
    Constrói a query SQL com placeholders nomeados (:nome).

    Retorna tupla (sql, params). Os valores reais NUNCA são interpolados
    na string — vão ao driver como parâmetros bindados.

    ATENÇÃO — MariaDB e LIMIT:
    O driver mariadb-connector não aceita LIMIT com placeholder nomeado
    via SQLAlchemy text(). Por isso o LIMIT é validado como int e embutido
    diretamente na string — seguro porque passa por int() antes.
    """
    group = parsed["group_by"]
    order = parsed["order"]
    params: dict = dict(parsed.get("params", {}))

    # Whitelist de colunas permitidas no GROUP BY
    allowed_groups = {"canal", "equipamento", "tipo_erro"}
    if group not in allowed_groups:
        group = "canal"

    # ORDER BY restrito a ASC/DESC
    if order not in {"ASC", "DESC"}:
        order = "DESC"

    # LIMIT: forçar int + range check elimina possibilidade de injeção
    limit = int(parsed.get("limit", 50))
    if limit < 1 or limit > 1000:
        limit = 50

    where_fragments = parsed.get("where", [])
    where_clause = " AND ".join(where_fragments) if where_fragments else "1=1"

    sql = f"""
SELECT {group}, COUNT(*) AS total
FROM logs
WHERE {where_clause}
GROUP BY {group}
ORDER BY total {order}
LIMIT {limit}
""".strip()

    return sql, params