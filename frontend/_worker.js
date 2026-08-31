// Worker proxy para registrodevandalos.pages.dev
// Redirige /api/* al backend

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    if (url.pathname.startsWith('/api/')) {
      // Redirect to the tunnel backend
      return Response.redirect(`https://registro.mapadata.cl${url.pathname}${url.search}`, 302);
    }
    
    // Serve frontend
    return env.ASSETS.fetch(request);
  }
};
