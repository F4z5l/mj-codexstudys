const mongoose = require('mongoose');

const QuizSchema = new mongoose.Schema({
  testName: { type: String, unique: true },
  timeLimit: { type: Number, default: 600 },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Quiz', QuizSchema);
