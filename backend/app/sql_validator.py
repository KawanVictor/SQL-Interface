import re

BLOCKED_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",              # MariaDB: CALL proc() executa stored procedures
    r"\bSHOW\b",              # MariaDB: SHOW TABLES, SHOW DATABASES
    r"\bDESCRIBE\b",
    r"\bEXPLAIN\b",
    r"\bSET\b",               # MariaDB: SET GLOBAL/SESSION pode alterar configurações
    r"\bXP_\w+",
    r"--",                    # comentário inline SQL
    r"/\*",                   # comentário de bloco
    r";\s*\S",                # stacked queries
    r"\bINTO\b\s+\bOUTFILE\b",
    r"\bINTO\b\s+\bDUMPFILE\b",  # variante MariaDB
    r"\bLOAD_FILE\b",
    r"\bLOAD\b\s+\bDATA\b",
    r"\bCONNECTION_ID\b",
    r"\bSLEEP\b",             # blind injection via SLEEP()
    r"\bBENCHMARK\b",         # DoS via BENCHMARK()
]

ALLOWED_TABLES = {"logs"}


def validate_sql(sql: str) -> str:
    """
    Valida que o SQL gerado é seguro para execução no MariaDB.
    Lança ValueError com mensagem descritiva em caso de violação.
    """
    sql_stripped = sql.strip()

    if not sql_stripped.upper().startswith("SELECT"):
        raise ValueError("Somente consultas SELECT são permitidas.")

    sql_upper = sql_stripped.upper()

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            raise ValueError(f"Padrão não permitido na query: '{pattern}'")

    from_tables  = re.findall(r"\bFROM\s+(\w+)", sql_upper)
    join_tables  = re.findall(r"\bJOIN\s+(\w+)", sql_upper)
    referenced   = {t.lower() for t in from_tables + join_tables}
    unauthorized = referenced - ALLOWED_TABLES

    if unauthorized:
        raise ValueError(f"Tabela não autorizada: {unauthorized}")

    return sql_stripped