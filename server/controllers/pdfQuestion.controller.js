const fs = require('fs');
const pdf = require('pdf-parse');

exports.extractQuestions = async (filePath) => {
  const dataBuffer = fs.readFileSync(filePath);
  const data = await pdf(dataBuffer);

  // split by pages
  const pages = data.text.split('

');

  return pages.map((q, index) => ({
    qno: index + 1,
    question: q.trim()
  }));
};
