import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  // O navegador chama /api e o Vite repassa ao backend, então não depende de CORS
  const proxy = {
    "/api": {
      target: env.BACKEND_URL || "http://localhost:8000",
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ""),
    },
  };

  return {
    plugins: [react()],
    server: { port: 5173, proxy },
    preview: { port: 5173, proxy },
  };
});
