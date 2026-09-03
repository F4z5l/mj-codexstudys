const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');

const uploadRoutes = require('./routes/upload.routes');
const quizRoutes = require('./routes/quiz.routes');

const app = express();
connectDB();

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

app.use('/api/upload', uploadRoutes);
app.use('/api/quiz', quizRoutes);

app.get('/:testName', (req, res) => {
  res.sendFile(__dirname + '/../public/quiz.html');
});

module.exports = app;
