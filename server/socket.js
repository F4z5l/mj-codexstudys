const { Server } = require('socket.io');
const Quiz = require('./models/Quiz');

function initSocket(server) {
  const io = new Server(server);

  io.on('connection', socket => {
    socket.on('join-quiz', async testName => {
      socket.join(testName);
      const quiz = await Quiz.findOne({ testName });
      socket.emit('question', quiz.questions[quiz.currentQuestionIndex]);
    });

    socket.on('next-question', async testName => {
      const quiz = await Quiz.findOne({ testName });
      quiz.currentQuestionIndex++;
      await quiz.save();

      io.to(testName).emit('question', quiz.questions[quiz.currentQuestionIndex]);
    });
  });
}

module.exports = { initSocket };
