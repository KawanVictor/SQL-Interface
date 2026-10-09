const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// FastAPI devolve `detail` como string (HTTPException) ou lista (validação 422)
function readDetail(body, status) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).join("; ");
  }
  return `A API respondeu com erro ${status}.`;
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, options);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError(
      "Não foi possível conectar à API. Verifique se o backend está rodando.",
      0,
    );
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(readDetail(body, response.status), response.status);
  }
  return body;
}

export function runQuery(question, signal) {
  return request("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
}

export function checkHealth(signal) {
  return request("/health", { signal });
}
