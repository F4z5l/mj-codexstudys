// Live Quiz logic - 1 question at a time
const socket = io();
const testName = location.pathname.replace("/", "");
let username = "";

function startQuiz() {
    username = document.getElementById("name").value.trim();
    if (!username) return alert("Enter your name");

    socket.emit("join-quiz", testName);
}

socket.on("question", q => {
    document.getElementById("question").innerText = q ? q.question : "Quiz Ended";
});

function nextQuestion() {
    socket.emit("next-question", testName);
}
