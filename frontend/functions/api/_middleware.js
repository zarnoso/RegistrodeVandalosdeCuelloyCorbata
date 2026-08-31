// Worker para registrodevandalos.pages.dev
export default {
  async fetch(request) {
    const url = new URL(request.url);
    
    if (url.pathname.startsWith('/api/') || url.pathname === '/health') {
      return fetch('https://registro.mapadata.cl' + url.pathname + url.search, {
        method: request.method,
        headers: request.headers,
      });
    }
    
    return env.ASSETS.fetch(request);
  }
};
