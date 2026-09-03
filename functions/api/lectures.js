export async function onRequest(context) {
    const { request } = context;
    const url = new URL(request.url);
    
    const referer = request.headers.get('referer') || '';
    const origin = request.headers.get('origin') || '';
    const clientKey = url.searchParams.get('key');

    const batchId = url.searchParams.get('batchId');
    const subjectId = url.searchParams.get('subjectId');
    const page = url.searchParams.get('page') || 1;
    const contentType = url.searchParams.get('contentType') || 'notes';
    const tag = url.searchParams.get('tag') || '';

    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json; charset=utf-8'
    };

    if (request.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers });
    }

    if (clientKey !== 'TheDevcoderZ') {
        return new Response(JSON.stringify({ error: "Unauthorized access. Invalid key." }), { status: 403, headers });
    }

    if (!referer.includes('devcoderz-pw-7lw.pages.dev') && !origin.includes('devcoderz-pw-7lw.pages.dev')) {
        return new Response(JSON.stringify({ error: "Forbidden request source." }), { status: 403, headers });
    }

    if (!batchId || !subjectId) {
        return new Response(JSON.stringify({ error: "Missing required parameters" }), { status: 400, headers });
    }

    try {
        const targetUrl = `https://learnbyakp.onrender.com/api/penpencil/v2/batches/${encodeURIComponent(batchId)}/subject/${encodeURIComponent(subjectId)}/contents?page=${encodeURIComponent(page)}&contentType=${encodeURIComponent(contentType)}&tag=${encodeURIComponent(tag)}`;

        const response = await fetch(targetUrl, {
            headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            return new Response(JSON.stringify({ error: `External API responded with status ${response.status}` }), { status: response.status, headers });
        }

        const data = await response.json();

        const jsonString = JSON.stringify(data);
        const encodedData = btoa(encodeURIComponent(jsonString));

        return new Response(JSON.stringify({ encryptedData: encodedData }), { status: 200, headers });
    } catch (e) {
        return new Response(JSON.stringify({ error: "Internal Server Error", details: e.message }), { status: 500, headers });
    }
}
