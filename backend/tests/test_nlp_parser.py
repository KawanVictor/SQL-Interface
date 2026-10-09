import pytest

from app.nlp_parser import parse_question


def test_defaults():
    parsed = parse_question("quais canais tiveram falhas")
    assert parsed == {
        "group_by": "canal",
        "where": [],
        "params": {},
        "order": "DESC",
        "limit": 50,
    }


@pytest.mark.parametrize(
    "question, expected",
    [
        ("falhas por canal", "canal"),
        ("equipamentos com mais erros", "equipamento"),
        ("falhas por equipamento", "equipamento"),
        ("tipos de erro mais comuns", "tipo_erro"),
        ("erros por tipo de erro", "tipo_erro"),
    ],
)
def test_group_by(question, expected):
    assert parse_question(question)["group_by"] == expected


@pytest.mark.parametrize(
    "question, expected",
    [
        ("erros críticos", "critico"),
        ("erros criticos", "critico"),
        ("falhas críticas hoje", "critico"),
        ("erros de severidade alta", "alta"),
        ("erros de severidade média", "media"),
        ("erros de severidade baixa", "baixa"),
    ],
)
def test_severidade(question, expected):
    parsed = parse_question(question)
    assert "severidade = :severidade" in parsed["where"]
    assert parsed["params"]["severidade"] == expected


@pytest.mark.parametrize(
    "question",
    [
        "canais com falta de sinal",
        "canais com mais faltas de sinal",
        "canais com mais falhas",
    ],
)
def test_palavra_parecida_nao_vira_severidade(question):
    parsed = parse_question(question)
    assert "severidade" not in parsed["params"]


@pytest.mark.parametrize(
    "question, expected",
    [
        ("falhas nos últimos 7 dias", 7),
        ("falhas nos últimos sete dias", 7),
        ("falhas nos últimos 30 dias", 30),
        ("falhas nos últimos trinta dias", 30),
        ("falhas nos últimos 15 dias", 15),
        ("falhas no último 1 dia", 1),
    ],
)
def test_filtro_de_dias(question, expected):
    parsed = parse_question(question)
    assert parsed["where"] == ["data_evento >= DATE_SUB(NOW(), INTERVAL :dias DAY)"]
    assert parsed["params"] == {"dias": expected}


def test_dias_fora_do_intervalo_sao_ignorados():
    assert parse_question("falhas nos últimos 999 dias")["where"] == []


def test_hoje_tem_prioridade_sobre_dias():
    parsed = parse_question("falhas hoje nos últimos 30 dias")
    assert parsed["where"] == ["DATE(data_evento) = CURDATE()"]
    assert parsed["params"] == {}


def test_filtro_de_canal():
    parsed = parse_question("falhas da Globo")
    assert "LOWER(canal) = :canal" in parsed["where"]
    assert parsed["params"]["canal"] == "globo"


def test_palavra_parecida_nao_vira_canal():
    assert "canal" not in parse_question("bandas com erro")["params"]


@pytest.mark.parametrize(
    "question",
    ["falhas no rewrapper-01", "falhas no Rewrapper-01?", "falhas no rewrapper-01."],
)
def test_filtro_de_equipamento_ignora_pontuacao(question):
    parsed = parse_question(question)
    assert "LOWER(equipamento) LIKE :equipamento" in parsed["where"]
    assert parsed["params"]["equipamento"] == "%rewrapper-01%"


@pytest.mark.parametrize(
    "question, expected",
    [
        ("canais com mais falhas", "DESC"),
        ("canais com menos falhas", "ASC"),
    ],
)
def test_ordenacao(question, expected):
    assert parse_question(question)["order"] == expected


@pytest.mark.parametrize(
    "question, expected",
    [
        ("top 5 equipamentos", 5),
        ("os 3 primeiros canais", 3),
        ("top canais com mais falhas", 50),
        ("top 5 canais nos últimos 7 dias", 5),
    ],
)
def test_limite(question, expected):
    assert parse_question(question)["limit"] == expected


def test_valor_do_usuario_nunca_entra_no_sql():
    parsed = parse_question("globo'; DROP TABLE logs; -- rewrapper-01")
    assert all("DROP" not in fragment.upper() for fragment in parsed["where"])
    assert parsed["params"] == {"canal": "globo", "equipamento": "%rewrapper-01%"}
