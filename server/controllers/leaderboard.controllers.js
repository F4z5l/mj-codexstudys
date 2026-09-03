const UserAttempt = require('../models/UserAttempt');

exports.getLeaderboard = async (req, res) => {
    try {
        const { testName } = req.params;

        const attempts = await UserAttempt.find({ testName })
            .sort({ score: -1, submittedAt: 1 });

        const ranked = attempts.map((u, i) => ({
            rank: i + 1,
            name: u.username,
            score: u.score
        }));

        res.json(ranked);
    } catch (err) {
        console.error(err);
        res.status(500).json({ success: false, message: "Server error" });
    }
};
