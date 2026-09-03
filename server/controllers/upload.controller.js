// server/controllers/upload.controller.js
exports.uploadPDF = (req, res) => {
    if (!req.file) return res.status(400).json({ success: false, message: "No file uploaded" });
    res.json({ success: true, filename: req.file.filename });
};
