// Generate Quiz button logic
async function generateQuiz() {
    const testName = prompt("Enter Test Name (e.g., Live-RTS-01)");
    if (!testName) return alert("Test name required");

    const pdfInput = document.getElementById("pdf");
    if (!pdfInput.files[0]) return alert("Upload PDF first");

    const formData = new FormData();
    formData.append("pdf", pdfInput.files[0]);

    // Upload PDF first
    const uploadRes = await fetch("/api/upload", {
        method: "POST",
        body: formData
    });
    const uploadData = await uploadRes.json();
    if (!uploadData.success) return alert("PDF upload failed");

    // Create Quiz
    const quizRes = await fetch("/api/quiz/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            testName,
            pdfName: uploadData.filename
        })
    });

    const quizData = await quizRes.json();
    if (quizData.success) {
        alert("Quiz Created! Link: " + quizData.link);
        window.location.href = quizData.link;
    } else {
        alert("Quiz creation failed");
    }
}
