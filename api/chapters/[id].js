export default async function handler(req, res) {
  // CORS
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(204).end();

  try {
    const { id } = req.query; // ✅ BOOK_ID
    if (!id) return res.status(400).json({ error: "Missing book id" });

    const url = `https://auth.ssccglpinnacle.com/api/chapters-ebook/${encodeURIComponent(id)}`;

    const r = await fetch(url, {
      method: "GET",
      redirect: "follow",
      headers: {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0",
        // kabhi-kabhi upstream ko referer/origin chahiye hota hai:
        "referer": "https://ebooks.ssccglpinnacle.com/",
        "origin": "https://ebooks.ssccglpinnacle.com"
      }
    });

    const text = await r.text();

    // Debug help: agar upstream error de to tumhe yahin dikhe
    res.setHeader("X-Upstream-Status", String(r.status));

    // Content-Type set (important for res.json parsing)
    res.setHeader("Content-Type", "application/json; charset=utf-8");

    return res.status(r.status).send(text);
  } catch (e) {
    return res.status(500).json({ error: "Proxy error", message: String(e?.message || e) });
  }
}
