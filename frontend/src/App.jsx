import { useEffect, useRef, useState } from "react";

import { checkHealth, runQuery } from "./api.js";

const EXAMPLES = [
  "top canais com mais falhas nos últimos 7 dias",
  "equipamentos com mais erros críticos",
  "falhas da Globo nos últimos 30 dias",
  "canais com menos falhas hoje",
  "erros de severidade alta por equipamento",
];

const COLUMN_LABELS = {
  canal: "Canal",
  equipamento: "Equipamento",
  tipo_erro: "Tipo de erro",
};

const HISTORY_KEY = "text-to-sql:history";
const HISTORY_SIZE = 8;
const HEALTH_INTERVAL_MS = 15000;
const MIN_LENGTH = 3;
const MAX_LENGTH = 500;

function loadHistory() {
  try {
    const stored = JSON.parse(localStorage.getItem(HISTORY_KEY));
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
}

function saveHistory(history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch {
    // armazenamento indisponível (aba privada): o histórico vale só para a sessão
  }
}

function useApiStatus() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function ping() {
      try {
        await checkHealth(controller.signal);
        setStatus("online");
      } catch (error) {
        if (error.name !== "AbortError") setStatus("offline");
      }
    }

    ping();
    const timer = setInterval(ping, HEALTH_INTERVAL_MS);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, []);

  return status;
}

function StatusBadge({ status }) {
  const labels = {
    checking: "Verificando API…",
    online: "API online",
    offline: "API offline",
  };
  return (
    <span className={`status status-${status}`} role="status">
      <span className="status-dot" aria-hidden="true" />
      {labels[status]}
    </span>
  );
}

function ResultTable({ data }) {
  const groupKey = Object.keys(data[0]).find((key) => key !== "total");
  const max = Math.max(...data.map((row) => Number(row.total)), 1);

  return (
    <table className="results">
      <thead>
        <tr>
          <th scope="col">{COLUMN_LABELS[groupKey] ?? groupKey}</th>
          <th scope="col" className="num">
            Total
          </th>
          <th scope="col" aria-hidden="true" />
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr key={String(row[groupKey])}>
            <th scope="row">{String(row[groupKey])}</th>
            <td className="num">{Number(row.total).toLocaleString("pt-BR")}</td>
            <td className="bar-cell" aria-hidden="true">
              <span
                className="bar"
                style={{ width: `${(Number(row.total) / max) * 100}%` }}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SqlPanel({ sql, params }) {
  const [copied, setCopied] = useState(false);
  const entries = Object.entries(params ?? {});

  async function copy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // sem permissão de clipboard: o SQL continua selecionável na tela
    }
  }

  return (
    <section className="card" aria-labelledby="sql-title">
      <div className="card-header">
        <h2 id="sql-title">SQL gerado</h2>
        <button type="button" className="ghost" onClick={copy}>
          {copied ? "Copiado ✓" : "Copiar"}
        </button>
      </div>
      <pre className="sql">
        <code>{sql}</code>
      </pre>
      {entries.length > 0 && (
        <dl className="params">
          {entries.map(([name, value]) => (
            <div key={name}>
              <dt>:{name}</dt>
              <dd>{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

export default function App() {
  const apiStatus = useApiStatus();
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState(loadHistory);
  const requestRef = useRef(null);

  useEffect(() => () => requestRef.current?.abort(), []);

  async function ask(text) {
    const trimmed = text.trim();
    if (trimmed.length < MIN_LENGTH) {
      setError(`Digite uma pergunta com pelo menos ${MIN_LENGTH} caracteres.`);
      return;
    }

    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;

    setQuestion(trimmed);
    setLoading(true);
    setError(null);

    try {
      const response = await runQuery(trimmed, controller.signal);
      setResult({ ...response, question: trimmed });
      setHistory((previous) => {
        const next = [trimmed, ...previous.filter((item) => item !== trimmed)].slice(
          0,
          HISTORY_SIZE,
        );
        saveHistory(next);
        return next;
      });
    } catch (requestError) {
      if (requestError.name === "AbortError") return;
      setResult(null);
      setError(requestError.message);
    } finally {
      if (requestRef.current === controller) setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    ask(question);
  }

  function clearHistory() {
    setHistory([]);
    saveHistory([]);
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Text to SQL</h1>
          <p className="subtitle">
            Pergunte em português sobre os logs de falhas de transmissão.
          </p>
        </div>
        <StatusBadge status={apiStatus} />
      </header>

      <main>
        <form className="card ask" onSubmit={handleSubmit}>
          <label htmlFor="question">Sua pergunta</label>
          <div className="ask-row">
            <input
              id="question"
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ex.: top canais com mais falhas nos últimos 7 dias"
              maxLength={MAX_LENGTH}
              autoComplete="off"
              autoFocus
            />
            <button type="submit" className="primary" disabled={loading}>
              {loading ? "Consultando…" : "Consultar"}
            </button>
          </div>

          <div className="chips" aria-label="Exemplos de perguntas">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                className="chip"
                onClick={() => ask(example)}
              >
                {example}
              </button>
            ))}
          </div>
        </form>

        {error && (
          <div className="alert" role="alert">
            <span aria-hidden="true">⚠</span>
            <span>{error}</span>
          </div>
        )}

        {result && (
          <>
            <section className="card" aria-labelledby="result-title" aria-busy={loading}>
              <div className="card-header">
                <h2 id="result-title">Resultado</h2>
                <span className="muted">
                  {result.rows === 1 ? "1 linha" : `${result.rows} linhas`}
                </span>
              </div>
              <p className="asked">“{result.question}”</p>
              {result.data.length > 0 ? (
                <ResultTable data={result.data} />
              ) : (
                <p className="empty">Nenhum registro encontrado para essa pergunta.</p>
              )}
            </section>

            <SqlPanel sql={result.sql} params={result.params} />
          </>
        )}

        {history.length > 0 && (
          <section className="card" aria-labelledby="history-title">
            <div className="card-header">
              <h2 id="history-title">Perguntas recentes</h2>
              <button type="button" className="ghost" onClick={clearHistory}>
                Limpar
              </button>
            </div>
            <ul className="history">
              {history.map((item) => (
                <li key={item}>
                  <button type="button" onClick={() => ask(item)}>
                    {item}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}
