export async function onRequest(context) {
    const { request } = context;
    const url = new URL(request.url);

    const referer = request.headers.get('referer') || '';
    const origin = request.headers.get('origin') || '';
    const clientKey = url.searchParams.get('key');
    const batchId = url.searchParams.get('batchId');
    const subjectId = url.searchParams.get('subjectId');

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
        return new Response(JSON.stringify({ error: "Required parameters missing." }), { status: 400, headers });
    }

    try {
        const targetUrl = `https://eduvibe-pw-api.wasmer.app/chapters.php?batch_id=${batchId}&subject_id=${subjectId}`;
        const response = await fetch(targetUrl, {
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });

        if (!response.ok) throw new Error();
        const data = await response.json();

        const jsonString = JSON.stringify(data);
        const encodedData = btoa(encodeURIComponent(jsonString));

        return new Response(JSON.stringify({ encryptedData: encodedData }), { status: 200, headers });
    } catch (e) {
        return new Response(JSON.stringify({ error: "Failed to fetch data." }), { status: 500, headers });
    }
}