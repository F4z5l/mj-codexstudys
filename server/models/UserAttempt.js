const mongoose = require('mongoose');

const AttemptSchema = new mongoose.Schema({
  username: String,
  testName: String,
  score: Number,
  attemptCount: Number,
  submittedAt: Date
});

module.exports = mongoose.model('UserAttempt', AttemptSchema);
