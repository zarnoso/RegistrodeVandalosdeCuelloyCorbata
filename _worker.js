// Cloudflare Worker Proxy - Registro de Vándalos
// Redirige /api/* al backend en localhost:8005

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    // Servir el frontend para rutas no-API
    if (!url.pathname.startsWith('/api/') && !url.pathname.startsWith('/health')) {
      return fetch(request);
    }
    
    // Redirigir al backend
    const backendUrl = `http://192.168.100.23:8005${url.pathname}${url.search}`;
    
    try {
      const response = await fetch(backendUrl, {
        method: request.method,
        headers: request.headers,
      });
      
      const body = await response.text();
      
      return new Response(body, {
        status: response.status,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        }
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: 'Backend unreachable', detail: e.message }), {
        status: 502,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
  }
};
