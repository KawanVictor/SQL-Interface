def parse_question(question: str) -> dict:
    """
    Interpreta a pergunta em linguagem natural e devolve:
      - group_by : coluna para agrupamento
      - where    : lista de fragmentos SQL (com placeholders :nome)
      - params   : dict com os valores reais (nunca interpolados na string)
      - order    : ASC | DESC
      - limit    : int

    Separar `where` de `params` é o que evita SQL injection:
    os valores reais nunca tocam na string SQL — vão direto para o driver.
    """
    q = question.lower()

    parsed: dict = {
        "group_by": "canal",
        "where": [],
        "params": {},
        "order": "DESC",
        "limit": 50,
    }

    # --- agrupamento ---
    if "equipamento" in q:
        parsed["group_by"] = "equipamento"

    # --- filtros de data ---
    if "hoje" in q:
        parsed["where"].append("DATE(data_evento) = CURDATE()")

    if "7 dias" in q or "sete dias" in q:
        parsed["where"].append("data_evento >= DATE_SUB(NOW(), INTERVAL 7 DAY)")

    if "30 dias" in q or "trinta dias" in q:
        parsed["where"].append("data_evento >= DATE_SUB(NOW(), INTERVAL 30 DAY)")

    # --- filtro de severidade (valor via parâmetro, nunca interpolado) ---
    if "critico" in q or "crítico" in q:
        parsed["where"].append("severidade = :severidade")
        parsed["params"]["severidade"] = "critico"
    elif "media" in q or "média" in q:
        parsed["where"].append("severidade = :severidade")
        parsed["params"]["severidade"] = "media"
    elif "alta" in q:
        parsed["where"].append("severidade = :severidade")
        parsed["params"]["severidade"] = "alta"

    # --- filtro de canal (valor via parâmetro) ---
    canais_conhecidos = ["globo", "sportv", "discovery", "record", "band"]
    for canal in canais_conhecidos:
        if canal in q:
            parsed["where"].append("LOWER(canal) = :canal")
            parsed["params"]["canal"] = canal
            break

    # --- filtro de equipamento (valor via parâmetro) ---
    if "rewrapper" in q:
        for part in q.split():
            if part.startswith("rewrapper"):
                parsed["where"].append("LOWER(equipamento) LIKE :equipamento")
                parsed["params"]["equipamento"] = f"%{part}%"
                break

    # --- ordenação ---
    if "menos" in q:
        parsed["order"] = "ASC"
    else:
        parsed["order"] = "DESC"

    return parsed