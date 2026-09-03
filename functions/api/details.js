export async function onRequest(context) {
    const { request } = context;
    const url = new URL(request.url);
    
    const referer = request.headers.get('referer') || '';
    const origin = request.headers.get('origin') || '';
    const clientKey = url.searchParams.get('key');
    const batch_id = url.searchParams.get('batch_id');

    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Accept',
        'Content-Type': 'application/json; charset=utf-8'
    };

    if (request.method === 'OPTIONS') {
        return new Response(null, { status: 200, headers });
    }

    if (clientKey !== 'TheDevcoderZ') {
        return new Response(JSON.stringify({ success: false, error: "Unauthorized access. Invalid key." }), { status: 403, headers });
    }

    if (!referer.includes('devcoderz-pw-7lw.pages.dev') && !origin.includes('devcoderz-pw-7lw.pages.dev')) {
        return new Response(JSON.stringify({ success: false, error: "Forbidden request source." }), { status: 403, headers });
    }

    if (!batch_id) {
        return new Response(JSON.stringify({ success: false, error: "Batch ID missing" }), { status: 400, headers });
    }

    try {
        const targetUrl = `https://api.penpencil.co/v3/batches/${encodeURIComponent(batch_id)}/details?page=1`;

        const response = await fetch(targetUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0'
            }
        });

        if (!response.ok) throw new Error("Failed to fetch from core API");

        const data = await response.json();

        const jsonString = JSON.stringify(data);
        const encodedData = btoa(encodeURIComponent(jsonString));

        return new Response(JSON.stringify({ encryptedData: encodedData }), { status: 200, headers });
    } catch (error) {
        console.error(error);
        return new Response(JSON.stringify({ success: false, error: "Failed to fetch data" }), { status: 500, headers });
    }
}
