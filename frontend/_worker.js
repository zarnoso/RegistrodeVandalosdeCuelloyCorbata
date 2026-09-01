// Worker proxy para Cloudflare Pages
// Redirige /api/* al backend en localhost:8006

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Redirigir peticiones API al backend
    if (url.pathname.startsWith('/api/') || url.pathname === '/health') {
      return fetch('https://api.mapadata.cl' + url.pathname + url.search, {
        method: request.method,
        headers: request.headers,
      });
    }
    
    // Servir frontend estático
    return env.ASSETS.fetch(request);
  }
};
