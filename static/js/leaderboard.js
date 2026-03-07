/**
 * Hall of Fame leaderboard — GET /api/leaderboard, POST /api/scores.
 */

export async function loadLeaderboard() {
  try {
    const resp = await fetch('/api/leaderboard');
    if (!resp.ok) return;
    const rows = await resp.json();
    const list = document.getElementById('hof-list');
    if (!list) return;
    list.innerHTML = '';
    rows.forEach((row, idx) => {
      const li = document.createElement('li');
      const preset = row.preset_used ? ` (${row.preset_used.replace(/_/g, ' ')})` : '';
      li.textContent = `#${idx + 1}  ${row.player_name} — Gen ${row.generation}${preset}`;
      list.appendChild(li);
    });
  } catch (err) {
    console.warn('Leaderboard load failed:', err);
  }
}

export async function saveScore(name, generation, aliveCnt, preset, cells) {
  const resp = await fetch('/api/scores', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_name: name,
      preset_used: preset ?? null,
      generation,
      alive_count: aliveCnt,
      cells,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Save score HTTP ${resp.status}`);
  }
  return resp.json();
}
