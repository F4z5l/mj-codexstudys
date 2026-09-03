const Quiz = require('../models/Quiz');
const { extractQuestions } = require('./pdfQuestion.controller');

exports.createQuiz = async (req, res) => {
  const { testName, pdfName } = req.body;

  const questions = await extractQuestions(`uploads/${pdfName}`);

  const quiz = await Quiz.create({
    testName,
    questions,
    timeLimit: questions.length * 30 // 30 sec per question
  });

  res.json({
    link: `https://resonance-live-stream-xmtr.onrender.com/${testName}`
  });
};
