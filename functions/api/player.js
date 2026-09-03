export async function onRequest(context) {
  const { request } = context;
  
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  let batchId, subjectId, videoId;
  const urlObj = new URL(request.url);

  if (request.method === "POST") {
    try {
      const body = await request.json();
      batchId = body.batch_id || body.batchId;
      subjectId = body.subject_id || body.subjectId;
      videoId = body.video_id || body.videoId || body.lectureId || body.scheduleId;
    } catch (e) {
      return new Response(JSON.stringify({ error: "Invalid JSON body" }), { 
        status: 400, 
        headers: { ...corsHeaders, "Content-Type": "application/json" } 
      });
    }
  } else if (request.method === "GET") {
    const query = urlObj.searchParams;
    batchId = query.get("batch_id") || query.get("batchId");
    subjectId = query.get("subject_id") || query.get("subjectId");
    videoId = query.get("video_id") || query.get("videoId") || query.get("lectureId") || query.get("scheduleId");
  } else {
    return new Response(JSON.stringify({ error: "Method not allowed" }), { 
      status: 405, 
      headers: { ...corsHeaders, "Content-Type": "application/json" } 
    });
  }

  if (!batchId || !subjectId || !videoId) {
    return new Response(JSON.stringify({ error: "Missing required parameters" }), { 
      status: 400, 
      headers: { ...corsHeaders, "Content-Type": "application/json" } 
    });
  }

  const targetUrl = `https://rangexcoder-api.vercel.app/batch/${batchId}/subject/${subjectId}/video/${videoId}`;

  try {
    const apiRes = await fetch(targetUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
      }
    });

    const originalData = await apiRes.json();

    if (originalData && originalData.data) {
      delete originalData.data.proxiedVideoUrl;
    }

    return new Response(JSON.stringify(originalData), { 
      status: 200, 
      headers: { ...corsHeaders, "Content-Type": "application/json" } 
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500, 
      headers: { ...corsHeaders, "Content-Type": "application/json" } 
    });
  }
}
