export default function handler(req, res) {
  // --- CORS ---
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // --- Data store ---
  const apps = {
    gyanbindu: {
      id: "gyanbindu",
      domain: "gyanbinduapi.appx.co.in",
      name: "GYAN BINDU",
      "stylishName(brand)": "GYAN +BINDU",
      image: "",
      token: "",
      courseid: 37,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
  lakshay: {
    "id": "lakshay",
    "domain": "lakshyaclassesapi.appx.co.in",
    "name": "LAKSHAY CLASSES",
    "stylishName(brand)": "LAKSHAY +CLASSES",
    "image": "",
    "token": "",
    "courseid": 732,
    "player_url": "../imp/player",
    "pdf_view_api": "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
    "pdf_dow_api": "https://pdf-appx.edumate.life/?url="
} 
  pa: {
    "id": "pa",
    "domain": "parmaracademyapi.classx.co.in",
    "name": "PARAM +ACADEMY",
    "stylishName(brand)": "PARAM +ACADEMY",
    "image": "",
    "token": "",
    "courseid": 40,
    "player_url": "../imp/player",
    "pdf_view_api": "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
    "pdf_dow_api": "https://pdf-appx.edumate.life/?url="
},
  aash: {
    "id": "aash",
    "domain": "aashapi.appx.co.in",
    "name": "AASH +OFFICIAL",
    "stylishName(brand)": "AASH +OFFICIAL",
    "image": "",
    "token": "",
    "courseid": 552,
    "player_url": "../imp/player",
    "pdf_view_api": "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
    "pdf_dow_api": "https://pdf-appx.edumate.life/?url="
    },
    rozgar: {
      id: "rozgar",
      domain: "rozgarapinew.teachx.in",
      name: "ROJGAR WITH +ANKIT",
      "stylishName(brand)": "RWA",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    winnersinstitute: {
      id: "winnersinstitute",
      domain: "winnersinstituteapi.cloudflare.net.in",
      name: "Winner +Institute",
      "stylishName(brand)": "Winner Institute",
      image: "",
      token: "",
      courseid: 156,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    physicsumeshrajori: {
      id: "physicsumeshrajori",
      domain: "physicsumeshrajoriaapi.classx.co.in",
      name: "PHYSICS +UMESH",
      "stylishName(brand)": "PHYSICS WITH+UMESH RAJORIA",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    aastha_ias: {
      id: "aastha_ias",
      domain: "asthaiasacademyapi.classx.co.in",
      name: "AASTHA +IAS",
      "stylishName(brand)": "ASTHA IAS",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    exampur: {
      id: "exampur",
      domain: "crackexampurviapi.classx.co.in",
      name: "exampur",
      "stylishName(brand)": "EXAM+PUR",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    boosteracademy: {
      id: "boosteracademy",
      domain: "boosteracademyapi.classx.co.in",
      name: "BOOSTER ACADEMY",
      "stylishName(brand)": "BOOSTER +ACADEMY",
      image: "",
      token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjI2NzExOSIsInRpbWVzdGFtcCI6MTc3ODkzNTQxMiwiaXZfdmVyIjoyLCJzZXNzaW9uIjoiZXlKMGVYQWlPaUpLVjFRaUxDSmhiR2NpT2lKSVV6STFOaUo5LmV5SnBaQ0k2SWpJMk56RXhPU0lzSW1WdFlXbHNJam9pYlhWclpYTm9PR3BoY0RJd01EWkFaMjFoYVd3dVkyOXRJaXdpYm1GdFpTSTZJazExYTJWemFDQkRhRzkxWkdoaGNua2lMQ0owWlc1aGJuUlVlWEJsSWpvaWRYTmxjaUlzSW5SbGJtRnVkRTVoYldVaU9pSmliMjl6ZEdWeVlXTmhaR1Z0ZVY5a1lpSXNJblJsYm1GdWRFbGtJam9pSWl3aVpHbHpjRzl6WVdKc1pTSTZabUZzYzJWOS5QdWFCUUlyS185SUZWWkJWRFhCcDRkV25kMkpjUnRfSEY5YlRhVERJcEVNIn0.0E1mnrHSTqTecyyY851k4Z2weOSdEg99LYkGA94fxF4",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    dpsir: {
      id: "dpsir",
      domain: "mathsdpsirofficialapi.akamai.net.in",
      name: "DP SIR MATHS",
      "stylishName(brand)": "DP +SIR",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    alphainstitute: {
      id: "alphainstitute",
      domain: "alphainstituteproapi.classx.co.in",
      name: "ALPHA INSTITUTE PRO",
      "stylishName(brand)": "ALPHA +INSTITUTE",
      image: "",
      token: "",
      courseid: 59,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    RWA: {
      id: "RWA",
      domain: "rozgarapinew.teachx.in",
      name: "ROJGAR WITH ANKIT",
      "stylishName(brand)": "ROJGAR WITH +ANKIT",
      image: "https://mtaiirus-v2.lovable.app/__l5e/assets-v1/87aad433-8d08-44d9-be73-30658f34b830/mtaiirus-logo.jpg",
      token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjE0NDA2MzA2IiwidGltZXN0YW1wIjoxNzc3OTk5NjgzLCJpdl92ZXIiOjEsInNlc3Npb24iOiJleUowZVhBaU9pSktWMVFpTENKaGJHY2lPaUpJVXpJMU5pSjkuZXlKcFpDSTZJakUwTkRBMk16QTJJaXdpWlcxaGFXd2lPaUpoY201cGFHWjBZM2xtWkVCbWFHbHRiUzVqYjIwaUxDSnVZVzFsSWpvaVJYQmhjblZ1SUhOb1lYSnVZU0lzSW5SbGJtRnVkRlI1Y0dVaU9pSjFjMlZ5SWl3aWRHVnVZVzUwVG1GdFpTSTZJbkp2ZW1kaGNsOWtZaUlzSW5SbGJtRnVkRWxrSWpvaUlpd2laR2x6Y0c5ellXSnNaU0k2Wm1Gc2MyVjkuUVF3azVBSTZHYXZ0M2hFZHhrbkR5LUhBeDZ4ME1MOW9sQ2pwQnpxQW9XMCJ9.1Do6ZcvqA6XS662YgywMvHCjQmMLfwp55PIK1TJ8B7w",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    ankitsingh: {
      id: "ankitsingh",
      domain: "ankitsinghapi.classx.co.in",
      name: "ANKIT",
      "stylishName(brand)": "ANKIT +SINGH",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    sciencemagnet: {
      id: "sciencemagnet",
      domain: "sciencemagnetapi.classx.co.in",
      name: "SCIENCE MAGNET",
      "stylishName(brand)": "SCIENCE +MAGNET",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    springboard: {
      id: "springboard",
      domain: "springboardacademyapi.appx.co.in",
      name: "SPRING BOARD",
      "stylishName(brand)": "SPRING +BOARD",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    ashishsingh: {
      id: "ashishsingh",
      domain: "ashishsinghlecturesapi.teachx.in",
      name: "ASHISH SINGH LECTURES",
      "stylishName(brand)": "AS +Lectures",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    vidyagram: {
      id: "vidyagram",
      domain: "armathsapi.akamai.net.in",
      name: "VIDYAGRAM",
      "stylishName(brand)": "RW +ANKIT",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    },
    vkknowledge: {
      id: "vkknowledge",
      domain: "vkknowledgeelectricalapi.akamai.net.in",
      name: "VK KNOWLEDGE",
      "stylishName(brand)": "VK +KNOWLEDGE",
      image: "",
      token: "",
      courseid: 184,
      player_url: "../imp/player.html",
      pdf_view_api: "https://pdfweb.classx.co.in/pdfjs-latest/web/viewer.html?file=",
      pdf_dow_api: "https://pdf-appx.edumate.life/?url="
    }
    // Add more entries below, one per app:
    // 9999: { id: "9999", domain: "...", name: "...", "stylishName(brand)": "...", image: "", token: "", courseid: 0, player_url: "", pdf_view_api: "...", pdf_dow_api: "..." },
  };

  // --- Validate params ---
  const app = req.query.app;
  const i = req.query.i; // reserved param, currently unused in response

  if (!app) {
    res.status(400).json({ error: "Missing required parameter: app" });
    return;
  }

  const entry = apps[app];

  if (!entry) {
    res.status(404).json({ error: "app not found" });
    return;
  }

  res.status(200).json(entry);
}
