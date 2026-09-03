const router = require('express').Router();
const upload = require('../middlewares/upload.middleware');
const { uploadPDF } = require('../controllers/upload.controller');

router.post('/', upload.single('pdf'), uploadPDF);
module.exports = router;
