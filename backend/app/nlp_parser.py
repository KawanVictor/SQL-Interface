import re
import unicodedata

CANAIS_CONHECIDOS = {"globo", "sportv", "discovery", "record", "band"}

# Palavra (já sem acento) -> valor do ENUM severidade
SEVERIDADES = {
    "critico": "critico", "criticos": "critico", "critica": "critico", "criticas": "critico",
    "alta": "alta", "altas": "alta",
    "media": "media", "medias": "media",
    "baixa": "baixa", "baixas": "baixa",
}

DIAS_POR_EXTENSO = {"sete": 7, "trinta": 30}
MAX_DIAS = 365

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_DIAS_RE = re.compile(r"\b(\d{1,3}|sete|trinta)\s+dias?\b")
_LIMIT_RE = re.compile(r"\btop\s+(\d{1,4})\b|\b(\d{1,4})\s+(?:primeiros|primeiras|principais|maiores)\b")


def _normalize(text: str) -> str:
    """Minúsculas e sem acentos, para comparar 'crítico' e 'critico' da mesma forma."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


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

    A comparação é por palavra inteira, não por substring: "falta" não pode
    virar severidade "alta", nem "banda" virar o canal "band".
    """
    q = _normalize(question)
    tokens = _TOKEN_RE.findall(q)
    words = set(tokens)

    parsed: dict = {
        "group_by": "canal",
        "where": [],
        "params": {},
        "order": "DESC",
        "limit": 50,
    }

    # --- agrupamento ---
    if words & {"tipo", "tipos"}:
        parsed["group_by"] = "tipo_erro"
    elif words & {"equipamento", "equipamentos"}:
        parsed["group_by"] = "equipamento"

    # --- filtros de data (um só: "hoje" tem prioridade sobre "N dias") ---
    dias_match = _DIAS_RE.search(q)
    if "hoje" in words:
        parsed["where"].append("DATE(data_evento) = CURDATE()")
    elif dias_match:
        valor = dias_match.group(1)
        dias = DIAS_POR_EXTENSO.get(valor) or int(valor)
        if 1 <= dias <= MAX_DIAS:
            parsed["where"].append("data_evento >= DATE_SUB(NOW(), INTERVAL :dias DAY)")
            parsed["params"]["dias"] = dias

    # --- filtro de severidade (valor via parâmetro, nunca interpolado) ---
    for token in tokens:
        if token in SEVERIDADES:
            parsed["where"].append("severidade = :severidade")
            parsed["params"]["severidade"] = SEVERIDADES[token]
            break

    # --- filtro de canal (valor via parâmetro) ---
    for token in tokens:
        if token in CANAIS_CONHECIDOS:
            parsed["where"].append("LOWER(canal) = :canal")
            parsed["params"]["canal"] = token
            break

    # --- filtro de equipamento (valor via parâmetro) ---
    for token in tokens:
        if token.startswith("rewrapper"):
            parsed["where"].append("LOWER(equipamento) LIKE :equipamento")
            parsed["params"]["equipamento"] = f"%{token}%"
            break

    # --- ordenação ---
    if "menos" in words:
        parsed["order"] = "ASC"

    # --- limite ("top 5", "3 primeiros"); o range é validado no sql_builder ---
    limit_match = _LIMIT_RE.search(q)
    if limit_match:
        parsed["limit"] = int(limit_match.group(1) or limit_match.group(2))

    return parsed
