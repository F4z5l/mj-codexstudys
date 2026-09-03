const socket = io();

function createQuiz(){
  // API call
}

function nextQuestion(){
  socket.emit('next-question', document.getElementById('testName').value);
}
