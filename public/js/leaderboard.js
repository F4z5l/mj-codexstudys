fetch(`/api/leaderboard/${testName}`)
.then(r => r.json())
.then(data => {
  const table = document.getElementById('board');
  data.forEach(u => {
    table.innerHTML += `<tr><td>${u.rank}</td><td>${u.name}</td><td>${u.score}</td></tr>`;
  });
});
