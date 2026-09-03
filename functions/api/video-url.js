export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // CORS Headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
      "Access-Control-Allow-Headers": "*",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Endpoint: /api/video-url?batchId=...&subjectId=...&scheduleId=...
    if (url.pathname === "/api/video-url") {
      const batchId = url.searchParams.get("batchId");
      const subjectId = url.searchParams.get("subjectId");
      const scheduleId = url.searchParams.get("scheduleId");

      if (!batchId || !subjectId || !scheduleId) {
        return new Response(JSON.stringify({ error: "Missing required parameters" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      try {
        const targetUrl = `https://pw-stream.pages.dev/api/video-url?batchId=${batchId}&subjectId=${subjectId}&scheduleId=${scheduleId}`;
        const response = await fetch(targetUrl);
        const data = await response.json();

        if (!data.success) {
          return new Response(JSON.stringify({ error: "Failed to fetch upstream API", details: data }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }

        // Aapka worker ka domain auto-detect karega ya aap apna custom domain daal sakte hain
        const workerDomain = `${url.protocol}//${url.host}`;
        const proxyPrefix = `${workerDomain}/api/stream-proxy?url=`;

        const cleanResponse = {
          success: true,
          topic_name: data.topic_name || "Untitled Lecture",
          HLS_STREAM_URL: data.HLS_STREAM_URL ? proxyPrefix + encodeURIComponent(data.HLS_STREAM_URL) : null,
          DASH_STREAM_URL: data.DASH_STREAM_URL ? proxyPrefix + encodeURIComponent(data.DASH_STREAM_URL) : null,
          video_url: data.video_url ? proxyPrefix + encodeURIComponent(data.video_url) : null,
          clearKeys: data.clearKeys || {},
          notes: data.notes || [],
          slides: data.slides || []
        };

        return new Response(JSON.stringify(cleanResponse), {
          status: 200,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });

      } catch (err) {
        return new Response(JSON.stringify({ error: "Internal Server Error", message: err.message }), {
          status: 500,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
    }

    // Endpoint: /api/stream-proxy?url=...
    if (url.pathname === "/api/stream-proxy") {
      const targetUrl = url.searchParams.get("url");
      if (!targetUrl) {
        return new Response("Missing URL parameter", { status: 400, headers: corsHeaders });
      }

      try {
        const upstreamResponse = await fetch(targetUrl, {
          headers: {
            // Optional headers agar upstream block kare toh
            "User-Agent": request.headers.get("User-Agent") || "Mozilla/5.0"
          }
        });

        // Response headers ko pass karna zaroori hai streaming ke liye
        const newHeaders = new Headers(upstreamResponse.headers);
        Object.keys(corsHeaders).forEach(key => newHeaders.set(key, corsHeaders[key]));

        return new Response(upstreamResponse.body, {
          status: upstreamResponse.status,
          headers: newHeaders
        });
      } catch (e) {
        return new Response("Stream Proxy Error: " + e.message, { status: 500, headers: corsHeaders });
      }
    }

    return new Response("Not Found", { status: 404, headers: corsHeaders });
  },
};