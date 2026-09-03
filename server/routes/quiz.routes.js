const router = require('express').Router();
const Quiz = require('../models/Quiz');

router.post('/create', async (req, res) => {
  const { testName } = req.body;
  await Quiz.create({ testName });
  res.json({
    link: `https://resonance-live-stream-xmtr.onrender.com/${testName}`
  });
});

module.exports = router;
