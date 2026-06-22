// Shared rendering logic for all World Cup pages.
// Each page must define the following globals before this script runs:
//   teams          — array from the embedded data block
//   GAMES          — alias for the page's games constant
//   YEAR           — e.g. 2018, 2022, 2026
//   TEAM_ELOS      — object mapping team name → pre-tournament ELO
//   GAMESETS       — array of [label, lastGameNumber] pairs defining tournament phases
//   CONFEDERATIONS — ordered array of confederation name strings
//   tbody          — document.getElementById('games')
//   thead          — document.querySelector('#matches-view thead')

// Early guards — must run before confByTeam/flagByTeam are built from these globals.
// Full structural validation (GAMESETS ordering, team-name coverage, etc.) runs at the
// bottom of this file once all functions are defined.
if (typeof teams === 'undefined') throw new Error('shared.js: page must define "teams" before loading this script');
if (typeof GAMES === 'undefined') throw new Error('shared.js: page must define "GAMES" before loading this script');

const confByTeam = {};
for (const t of teams) confByTeam[t.name] = t.confederation;
const flagByTeam = {};
for (const t of teams) flagByTeam[t.name] = t.flag;

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const [, month, day] = dateStr.split('-').map(Number);
  return `${MONTHS[month - 1]} ${day}`;
}

function signedElo(val) {
  if (typeof val !== 'number') return '';
  return val >= 0 ? `+${val}` : String(val);
}

function eloCell(preElo, delta) {
  if (delta !== '') return preElo != null ? `${preElo}${delta}` : delta;
  return preElo != null ? String(preElo) : '';
}

const ELO_GRADIENT_MAX = 400;
function eloColor(value) {
  const ratio = Math.max(-1, Math.min(1, value / ELO_GRADIENT_MAX));
  if (ratio >= 0) return `rgb(${255 - ratio * 105}, 255, ${255 - ratio * 105})`;
  return `rgb(255, ${255 + ratio * 105}, ${255 + ratio * 105})`;
}

// Date, #, spacer, homeElo, homeFlag, homeScore, sep, awayScore, awayFlag, awayElo
const GAME_COL_COUNT = 10;
const matchState = { view: 'elo', colCount: GAME_COL_COUNT, expandRow: null, gameRow: null };

function gameColsHeader() {
  return (
    `<th class="narrow" rowspan="2">Date</th>` +
    `<th class="narrow" rowspan="2">#</th>` +
    `<th class="spacer" rowspan="2"></th>` +
    `<th colspan="3" rowspan="2" style="text-align:center">Home</th>` +
    `<th class="score-sep" rowspan="2"></th>` +
    `<th colspan="3" rowspan="2" style="text-align:center">Away</th>`
  );
}

function toggleCellHtml(colspan) {
  return `<th colspan="${colspan}" class="toggle-cell">` +
    `<div class="view-toggle">` +
    `<button data-view="elo"${matchState.view === 'elo' ? ' class="active"' : ''}>ELO Shift</button>` +
    `<button data-view="wld"${matchState.view === 'wld' ? ' class="active"' : ''}>W / D / L</button>` +
    `<button data-view="stats"${matchState.view === 'stats' ? ' class="active"' : ''}>Stats</button>` +
    `</div></th>`;
}

function gameRowCells(game) {
  const change = game.eloChange;
  const homeEloDelta = signedElo(change);
  const awayEloDelta = typeof change === 'number' ? signedElo(-change) : '';
  const homeScore = game.homeScore ?? '';
  const awayScore = game.awayScore ?? '';
  return (
    `<td class="narrow">${formatDate(game.date)}</td>` +
    `<td class="narrow">#${game.gameNumber}</td>` +
    `<td class="spacer"></td>` +
    `<td class="elo">${eloCell(game.homeEloPre, homeEloDelta)}</td>` +
    `<td class="flag"><span class="icon" style="background-image:url('data/flags/${flagByTeam[game.homeTeam]}.svg')" title="${esc(game.homeTeam)}"></span></td>` +
    `<td class="narrow">${homeScore}</td>` +
    `<td class="score-sep">-</td>` +
    `<td class="narrow">${awayScore}</td>` +
    `<td class="flag"><span class="icon" style="background-image:url('data/flags/${flagByTeam[game.awayTeam]}.svg')" title="${esc(game.awayTeam)}"></span></td>` +
    `<td class="elo">${eloCell(game.awayEloPre, awayEloDelta)}</td>`
  );
}

// eloChange sign convention (matches data schema): positive = home team gained ELO, negative = away team gained.
// Every place that reads eloChange must apply this same sign: home += eloChange, away -= eloChange.
function computeEloRowTotals(games, confederations) {
  const totals = {};
  for (const c of confederations) totals[c] = 0;
  const rowTotals = [];
  for (const game of games) {
    if (typeof game.eloChange === 'number') {
      const hc = confByTeam[game.homeTeam];
      const ac = confByTeam[game.awayTeam];
      if (hc) totals[hc] += game.eloChange;
      if (ac) totals[ac] -= game.eloChange;
    }
    rowTotals.push({ ...totals });
  }
  return rowTotals;
}

function computeWldRowTotals(games, confederations) {
  const totals = {};
  for (const c of confederations) totals[c] = { w: 0, d: 0, l: 0 };
  const rowTotals = [];
  for (const game of games) {
    const hs = game.homeScore;
    const as_ = game.awayScore;
    if (hs !== null && as_ !== null) {
      const hc = confByTeam[game.homeTeam];
      const ac = confByTeam[game.awayTeam];
      if (hs > as_) {
        if (hc) totals[hc].w++;
        if (ac) totals[ac].l++;
      } else if (as_ > hs) {
        if (ac) totals[ac].w++;
        if (hc) totals[hc].l++;
      } else {
        if (hc) totals[hc].d++;
        if (ac) totals[ac].d++;
      }
    }
    rowTotals.push(Object.fromEntries(confederations.map(c => [c, { ...totals[c] }])));
  }
  return rowTotals;
}

function wireToggle() {
  thead.querySelectorAll('.view-toggle button').forEach(btn => {
    btn.addEventListener('click', () => { matchState.view = btn.dataset.view; render(); });
  });
}

function render() {
  const games = GAMES;
  const participating = new Set();
  for (const game of games) {
    const hc = confByTeam[game.homeTeam];
    const ac = confByTeam[game.awayTeam];
    if (hc) participating.add(hc);
    if (ac) participating.add(ac);
  }
  const confederations = CONFEDERATIONS.filter(c => participating.has(c));

  tbody.innerHTML = '';
  matchState.expandRow = null;
  matchState.gameRow = null;

  if (games.length === 0) {
    thead.innerHTML = `<tr><th>No games</th></tr><tr></tr>`;
    tbody.innerHTML = `<tr><td>No games yet</td></tr>`;
    return;
  }

  // Build row-by-row ELO running totals once; derive column ordering from the last row.
  // Passing rowTotals into renderElo avoids a second identical walk over all games.
  const eloRowTotals = computeEloRowTotals(games, confederations);
  const finalTotals = eloRowTotals[eloRowTotals.length - 1];
  const ordered = [...confederations].sort((a, b) => (finalTotals[b] || 0) - (finalTotals[a] || 0));

  if (matchState.view === 'elo') renderElo(games, ordered, eloRowTotals);
  else if (matchState.view === 'wld') renderWld(games, ordered);
  else renderStats(games, ordered);

  wireToggle();
}

function renderElo(games, ordered, rowTotals) {
  const N = ordered.length;
  matchState.colCount = GAME_COL_COUNT + N;

  thead.innerHTML =
    `<tr>${gameColsHeader()}${toggleCellHtml(N)}</tr>` +
    `<tr>${ordered.map(c => `<th class="conf">${c}</th>`).join('')}</tr>`;

  games.forEach((game, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = gameRowCells(game) +
      ordered.map(c =>
        typeof game.eloChange === 'number'
          ? `<td class="num conf" style="background-color:${eloColor(rowTotals[i][c])}">${rowTotals[i][c]}</td>`
          : `<td class="num conf"></td>`
      ).join('');
    tr.addEventListener('click', () => toggleExpand(game, tr));
    tbody.appendChild(tr);
  });
}

function renderWld(games, ordered) {
  const rowTotals = computeWldRowTotals(games, ordered);
  const N = ordered.length;
  matchState.colCount = GAME_COL_COUNT + N;

  thead.innerHTML =
    `<tr>${gameColsHeader()}${toggleCellHtml(N)}</tr>` +
    `<tr>${ordered.map(c => `<th class="conf">${c}</th>`).join('')}</tr>`;

  games.forEach((game, i) => {
    const played = game.homeScore !== null && game.awayScore !== null;
    const tr = document.createElement('tr');
    tr.innerHTML = gameRowCells(game) +
      ordered.map(c => {
        if (!played) return `<td class="num conf"></td>`;
        const { w, l, d } = rowTotals[i][c];
        return `<td class="num conf">${w}-${d}-${l}</td>`;
      }).join('');
    tr.addEventListener('click', () => toggleExpand(game, tr));
    tbody.appendChild(tr);
  });
}

function renderStats(games, ordered) {
  const N = ordered.length;
  matchState.colCount = GAME_COL_COUNT + N;

  // Stat column definitions — trimmed to N if fewer than 3 confederations.
  const statDefs = [
    { label: 'Wins',  key: 'wins' },
    { label: 'Draws', key: 'draws' },
    { label: 'Win%',  key: 'pct'  },
  ].slice(0, N);
  const nStats = statDefs.length;
  const extra = N - nStats; // padding columns to reach N total

  const emptyTh = Array(extra).fill('<th class="conf"></th>').join('');
  thead.innerHTML =
    `<tr>${gameColsHeader()}${toggleCellHtml(N)}</tr>` +
    `<tr>${statDefs.map(d => `<th class="conf">${d.label}</th>`).join('')}${emptyTh}</tr>`;

  const emptyTd = Array(N).fill('<td class="num conf"></td>').join('');
  const extraTd = Array(extra).fill('<td class="num conf"></td>').join('');
  let wins = 0, draws = 0;
  games.forEach(game => {
    const hs = game.homeScore;
    const as_ = game.awayScore;
    const played = hs !== null && as_ !== null;
    const tr = document.createElement('tr');
    if (played) {
      if (hs !== as_) wins++;
      else draws++;
      const total = wins + draws;
      const pct = Math.round(wins / total * 100) + '%';
      const vals = { wins, draws, pct };
      tr.innerHTML = gameRowCells(game) +
        statDefs.map(d => `<td class="num conf">${vals[d.key]}</td>`).join('') + extraTd;
    } else {
      tr.innerHTML = gameRowCells(game) + emptyTd;
    }
    tr.addEventListener('click', () => toggleExpand(game, tr));
    tbody.appendChild(tr);
  });
}

function toggleExpand(game, tr) {
  const colCount = matchState.colCount;
  if (matchState.expandRow) {
    matchState.expandRow.remove();
    matchState.expandRow = null;
    if (matchState.gameRow === tr) { matchState.gameRow = null; return; }
  }
  matchState.gameRow = tr;
  const expandTr = document.createElement('tr');
  expandTr.className = 'expand-row';
  const td = document.createElement('td');
  td.colSpan = colCount;

  const hsVal = game.homeScore != null ? game.homeScore : '';
  const asVal = game.awayScore != null ? game.awayScore : '';
  const eloVal = game.eloChange != null ? Math.abs(game.eloChange) : '';
  const gainsVal = game.eloChange != null ? (game.eloChange >= 0 ? 'home' : 'away') : '';
  const isDraw = hsVal !== '' && asVal !== '' && hsVal === asVal;

  td.innerHTML = `
    <div class="ur-line"><strong>#${game.gameNumber}: ${esc(game.homeTeam)} vs ${esc(game.awayTeam)}</strong></div>
    <div class="ur-line">
      <label>Home score: <input class="ur-hs" type="number" min="0" value="${hsVal}"></label>
      <label>Away score: <input class="ur-as" type="number" min="0" value="${asVal}"></label>
      <label>ELO magnitude (opt): <input class="ur-elo" type="number" min="0" value="${eloVal}"></label>
      <label class="ur-gains-wrap" style="display:${isDraw ? 'flex' : 'none'}">Who gains ELO:
        <select class="ur-gains">
          <option value="" ${gainsVal === '' ? 'selected' : ''}>—</option>
          <option value="home" ${gainsVal === 'home' ? 'selected' : ''}>${esc(game.homeTeam)}</option>
          <option value="away" ${gainsVal === 'away' ? 'selected' : ''}>${esc(game.awayTeam)}</option>
        </select>
      </label>
    </div>
    <div class="ur-line">
      <button class="ur-gen">Generate command</button>
      <input class="ur-cmd" type="text" readonly placeholder="command will appear here">
      <button class="ur-copy">Copy</button>
    </div>`;

  td.addEventListener('click', e => e.stopPropagation());

  function updateGainsVisibility() {
    const hs = td.querySelector('.ur-hs').value;
    const as_ = td.querySelector('.ur-as').value;
    const draw = hs !== '' && as_ !== '' && hs === as_;
    td.querySelector('.ur-gains-wrap').style.display = draw ? 'flex' : 'none';
  }
  td.querySelector('.ur-hs').addEventListener('input', updateGainsVisibility);
  td.querySelector('.ur-as').addEventListener('input', updateGainsVisibility);

  td.querySelector('.ur-gen').addEventListener('click', () => {
    const hs = td.querySelector('.ur-hs').value;
    const as_ = td.querySelector('.ur-as').value;
    const elo = td.querySelector('.ur-elo').value;
    const gains = td.querySelector('.ur-gains').value;
    const draw = hs !== '' && as_ !== '' && hs === as_;
    let cmd = `python3 scripts/set_result.py ${YEAR} ${game.gameNumber} ${hs} ${as_}`;
    if (elo !== '') cmd += ` ${elo} --gains ${draw ? (gains || '???') : (Number(hs) > Number(as_) ? 'home' : 'away')}`;
    td.querySelector('.ur-cmd').value = cmd;
  });

  td.querySelector('.ur-copy').addEventListener('click', () => {
    const cmdInput = td.querySelector('.ur-cmd');
    cmdInput.select();
    navigator.clipboard.writeText(cmdInput.value);
  });

  expandTr.appendChild(td);
  tr.after(expandTr);
  matchState.expandRow = expandTr;
}

// ── Rankings view ──────────────────────────────────────────────────────────

function buildEloSnapshots() {
  const gamesByNumber = {};
  for (const g of GAMES) gamesByNumber[g.gameNumber] = g;

  const teamsInGameset = GAMESETS.map((_, i) => {
    if (i === 0) return null;
    const prevLast = GAMESETS[i - 1][1];
    const lastGame = GAMESETS[i][1];
    const s = new Set();
    for (let gn = prevLast + 1; gn <= lastGame; gn++) {
      const g = gamesByNumber[gn];
      if (g) { s.add(g.homeTeam); s.add(g.awayTeam); }
    }
    return s;
  });

  const eliminatedAfter = {};
  const allTeams = Object.keys(TEAM_ELOS);
  for (const team of allTeams) {
    let lastSeen = 0;
    for (let i = 1; i < GAMESETS.length; i++) {
      if (teamsInGameset[i] && teamsInGameset[i].has(team)) lastSeen = i;
    }
    eliminatedAfter[team] = lastSeen;
  }

  // ELO snapshots are derived from the pre-game ELOs written by build.py:
  //   post-game ELO for home team = homeEloPre + eloChange
  //   post-game ELO for away team = awayEloPre - eloChange
  // This makes the JS a reader of build.py's output rather than a parallel
  // reimplementation of the same chain, eliminating any risk of the two diverging.
  // Builds post-gameset ELO state by reading pre-game ELOs written by build.py.
  function applyGames(base, fromGn, toGn) {
    const next = { ...base };
    for (let gn = fromGn; gn <= toGn; gn++) {
      const g = gamesByNumber[gn];
      if (!g) continue;
      if (typeof g.eloChange === 'number') {
        if (g.homeEloPre !== null) next[g.homeTeam] = g.homeEloPre + g.eloChange;
        if (g.awayEloPre !== null) next[g.awayTeam] = g.awayEloPre - g.eloChange;
      }
    }
    return next;
  }

  const snapshots = [];
  // `baseline` is the ELO state after all completed gamesets; it carries forward
  // to teams that don't play in a given gameset.
  let baseline = { ...TEAM_ELOS };
  let liveFound = false;

  for (let i = 0; i < GAMESETS.length; i++) {
    if (i === 0) {
      snapshots.push({ label: 'Initial', complete: true, live: false, eloByTeam: { ...baseline } });
      continue;
    }
    const prevLast = GAMESETS[i - 1][1];
    const lastGame = GAMESETS[i][1];

    let allDone = true;
    for (let gn = prevLast + 1; gn <= lastGame; gn++) {
      const g = gamesByNumber[gn];
      if (!g) { console.warn(`shared.js: game #${gn} missing from data — treating gameset "${GAMESETS[i][0]}" as incomplete`); allDone = false; break; }
      if (g.eloChange === null) { allDone = false; break; }
    }

    if (allDone) {
      baseline = applyGames(baseline, prevLast + 1, lastGame);
      snapshots.push({ label: GAMESETS[i][0], complete: true, live: false, eloByTeam: { ...baseline } });
    } else if (!liveFound) {
      liveFound = true;
      const liveElo = applyGames(baseline, prevLast + 1, lastGame);
      const pendingTeams = new Set();
      for (let gn = prevLast + 1; gn <= lastGame; gn++) {
        const g = gamesByNumber[gn];
        if (g && g.eloChange === null) { pendingTeams.add(g.homeTeam); pendingTeams.add(g.awayTeam); }
      }
      snapshots.push({ label: GAMESETS[i][0], complete: false, live: true, eloByTeam: liveElo, pendingTeams });
    } else {
      snapshots.push({ label: GAMESETS[i][0], complete: false, live: false, eloByTeam: null });
    }
  }

  return { snapshots, eliminatedAfter };
}

function rankTeams(eloByTeam, prevRank) {
  const names = Object.keys(eloByTeam);
  names.sort((a, b) => {
    const diff = eloByTeam[b] - eloByTeam[a];
    if (diff !== 0) return diff;
    const pa = prevRank ? prevRank.indexOf(a) : -1;
    const pb = prevRank ? prevRank.indexOf(b) : -1;
    if (pa === -1 && pb === -1) return 0;
    if (pa === -1) return 1;
    if (pb === -1) return -1;
    return pa - pb;
  });
  return names;
}

const FLAG_PX_W = 35;
const FLAG_PX_H = 24;
const SCALE_GAP = 3;
const RANK_ROW_H = 36;

function scaleTopPx(elo, rawMin, rawMax, height) {
  const margin = RANK_ROW_H / 2;
  const drawH = height - 2 * margin - FLAG_PX_H;
  return Math.round(margin + drawH * (1 - (elo - rawMin) / (rawMax - rawMin)));
}

function maxClusterSizeForHeight(snapshots, ranked, rawMin, rawMax, height) {
  let maxSize = 1;
  snapshots.forEach((snap, si) => {
    if (!(snap.complete || snap.live) || !snap.eloByTeam || !ranked[si]) return;
    const tops = ranked[si]
      .map(team => scaleTopPx(snap.eloByTeam[team], rawMin, rawMax, height))
      .sort((a, b) => a - b);
    let lo = 0;
    for (let hi = 0; hi < tops.length; hi++) {
      while (tops[hi] - tops[lo] >= FLAG_PX_H) lo++;
      if (hi - lo + 1 > maxSize) maxSize = hi - lo + 1;
    }
  });
  return maxSize;
}

function computeScaleHeight(snapshots, ranked, rawMin, rawMax) {
  const MAX_H = 80000;
  if (maxClusterSizeForHeight(snapshots, ranked, rawMin, rawMax, MAX_H) >= 4) {
    return { height: MAX_H, hasError: true };
  }
  let lo = 100, hi = MAX_H;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (maxClusterSizeForHeight(snapshots, ranked, rawMin, rawMax, mid) >= 4) lo = mid;
    else hi = mid;
  }
  return { height: hi, hasError: false };
}

function computeTickStep(rawMin, rawMax, height) {
  const drawH = height - RANK_ROW_H;
  const pxPerElo = drawH / (rawMax - rawMin);
  const candidates = [200, 100, 50, 25, 10, 5, 2];
  for (const c of candidates) {
    const px = c * pxPerElo;
    if (px >= 150 && px <= 300) return c;
  }
  return candidates.reduce((best, c) =>
    Math.abs(c * pxPerElo - 200) < Math.abs(best * pxPerElo - 200) ? c : best
  );
}

const rankState = { view: 'rank', showElim: false, trueRank: false, model: null };

function setRankView(v) {
  rankState.view = v;
  document.getElementById('tab-rank').classList.toggle('active', v === 'rank');
  document.getElementById('tab-scale').classList.toggle('active', v === 'scale');
  updateRankingControls();
  renderRankings();
}

function toggleShowEliminated() {
  rankState.showElim = document.getElementById('chk-show-elim').checked;
  if (rankState.showElim) {
    rankState.trueRank = true;
    const chk = document.getElementById('chk-true-rank');
    if (chk) chk.checked = true;
  }
  updateRankingControls();
  renderRankings();
}

function toggleTrueRank() {
  rankState.trueRank = document.getElementById('chk-true-rank').checked;
  renderRankings();
}

function updateRankingControls() {
  const trueRankLabel = document.getElementById('true-rank-label');
  const trueRankChk = document.getElementById('chk-true-rank');
  if (!trueRankLabel || !trueRankChk) return;
  const isRank = rankState.view === 'rank';
  trueRankLabel.style.display = isRank ? '' : 'none';
}

// rankState.model is cached for the page lifetime — data is static (embedded at build time), so no invalidation needed.

function buildRankingsModel() {
  const { snapshots, eliminatedAfter } = buildEloSnapshots();

  const gnMap = {};
  for (const g of GAMES) gnMap[g.gameNumber] = g;
  const gamesByTeamInSnap = snapshots.map((snap, si) => {
    if (si === 0) return {};
    const prevLast = GAMESETS[si - 1][1];
    const lastGame = GAMESETS[si][1];
    const map = {};
    for (let gn = prevLast + 1; gn <= lastGame; gn++) {
      const g = gnMap[gn];
      if (g) { map[g.homeTeam] = g; map[g.awayTeam] = g; }
    }
    return map;
  });

  const ranked = [];
  let prevRank = null;
  for (const snap of snapshots) {
    if (snap.complete || snap.live) {
      const order = rankTeams(snap.eloByTeam, prevRank);
      ranked.push(order);
      prevRank = order;
    } else {
      ranked.push(prevRank);
    }
  }

  let rawMin = Infinity, rawMax = -Infinity;
  for (const snap of snapshots) {
    if (snap.eloByTeam) {
      for (const elo of Object.values(snap.eloByTeam)) {
        if (elo < rawMin) rawMin = elo;
        if (elo > rawMax) rawMax = elo;
      }
    }
  }

  const { height: scaleH, hasError: scaleHasError } = computeScaleHeight(snapshots, ranked, rawMin, rawMax);

  return { snapshots, eliminatedAfter, gamesByTeamInSnap, ranked, rawMin, rawMax, scaleH, scaleHasError };
}

function renderRankings() {
  if (!rankState.model) rankState.model = buildRankingsModel();
  const { snapshots, eliminatedAfter, gamesByTeamInSnap, ranked, rawMin, rawMax, scaleH, scaleHasError } = rankState.model;

  function buildTipHtml(team, elo, si) {
    const flag = flagByTeam[team] || '';
    const flagStyle = flag ? `background-image:url('data/flags/${flag}.svg')` : '';
    let html = `<div class="tip-flag" style="${flagStyle}"></div>`;
    html += `<div class="tip-name">${esc(team)}</div>`;
    html += `<div class="tip-elo-val">${elo !== null ? Math.round(elo) : '—'}</div>`;
    html += `<hr class="tip-sep">`;
    const g = si > 0 ? gamesByTeamInSnap[si][team] : null;
    const isHome = g && g.homeTeam === team;
    const opponent = g ? (isHome ? g.awayTeam : g.homeTeam) : null;
    html += `<div class="tip-label">Date</div><div class="tip-val">${g && g.date ? formatDate(g.date) : '—'}</div>`;
    html += `<div class="tip-label">Opponent</div><div class="tip-val">${opponent ? esc(opponent) : '—'}</div>`;
    if (g && typeof g.eloChange === 'number') {
      const score = isHome ? `${g.homeScore}–${g.awayScore}` : `${g.awayScore}–${g.homeScore}`;
      const delta = isHome ? g.eloChange : -g.eloChange;
      const cls = delta >= 0 ? 'tip-delta-pos' : 'tip-delta-neg';
      const sign = delta >= 0 ? '+' : '';
      html += `<div class="tip-label">Score</div><div class="tip-val">${score}</div>`;
      html += `<div class="tip-label">ELO</div><div class="tip-val"><span class="${cls}">${sign}${delta}</span></div>`;
    } else {
      html += `<div class="tip-label">Score</div><div class="tip-val">—</div>`;
      html += `<div class="tip-label">ELO</div><div class="tip-val">—</div>`;
    }
    return html;
  }

  const numTeams = ranked[0].length;
  const isScale = rankState.view === 'scale';

  // In compact rank mode (trueRank=off, showElim=off), the axis height is the
  // maximum number of visible teams in any single column. Group-stage columns
  // always show all teams, so for normal tournaments this equals numTeams.
  // Using an explicit max makes the code correct even if TEAM_ELOS ever
  // includes teams that appear in no game (they'd be in ranked[0] but never
  // assigned to a gameset, inflating numTeams beyond what the axis needs).
  const rankSlots = (() => {
    if (isScale || rankState.showElim || rankState.trueRank) return numTeams;
    let max = 0;
    snapshots.forEach((snap, si) => {
      if (!(snap.complete || snap.live) || !ranked[si]) return;
      let count = 0;
      for (const team of ranked[si]) {
        const elim = eliminatedAfter[team] > 0 && si > eliminatedAfter[team];
        if (!elim) count++;
      }
      if (count > max) max = count;
    });
    return max || numTeams;
  })();

  const bodyH = isScale ? scaleH : rankSlots * RANK_ROW_H;

  const header = document.getElementById('rankings-header');
  const body = document.getElementById('rankings-body');

  // Set grid columns dynamically based on number of gamesets
  const colTemplate = `4rem repeat(${snapshots.length}, minmax(111px, 1fr))`;
  header.style.gridTemplateColumns = colTemplate;
  body.style.gridTemplateColumns = colTemplate;

  header.innerHTML =
    `<div class="axis-head">${isScale ? '' : '#'}</div>` +
    snapshots.map(s => `<div>${s.label}</div>`).join('');

  body.innerHTML = '';

  const axisCol = document.createElement('div');
  axisCol.className = 'rankings-axis';
  axisCol.style.height = bodyH + 'px';

  const gridLineYs = [];
  if (isScale) {
    const step = computeTickStep(rawMin, rawMax, scaleH);
    const firstTick = Math.ceil(rawMin / step) * step;
    for (let tick = firstTick; tick <= rawMax; tick += step) {
      const y = scaleTopPx(tick, rawMin, rawMax, scaleH);
      gridLineYs.push(y);
      const lbl = document.createElement('div');
      lbl.className = 'axis-label';
      lbl.style.top = y + 'px';
      lbl.textContent = tick;
      axisCol.appendChild(lbl);
    }
  } else {
    for (let i = 0; i < rankSlots; i++) {
      const lbl = document.createElement('div');
      lbl.className = 'axis-label';
      lbl.style.top = (i * RANK_ROW_H + RANK_ROW_H / 2) + 'px';
      lbl.textContent = i + 1;
      axisCol.appendChild(lbl);
    }
    for (let n = 4; n < rankSlots; n += 4) {
      gridLineYs.push(n * RANK_ROW_H);
    }
  }

  function addGridLines(el) {
    gridLineYs.forEach(y => {
      const line = document.createElement('div');
      line.className = 'grid-line';
      line.style.top = y + 'px';
      el.appendChild(line);
    });
  }
  addGridLines(axisCol);
  body.appendChild(axisCol);

  const debugClustersCb = document.getElementById('debug-clusters');
  snapshots.forEach((snap, si) => {
    const col = document.createElement('div');
    col.className = 'snap-body-col';

    if ((snap.complete || snap.live) && ranked[si]) {
      const pinData = [];

      let compactSlot = 0;
      ranked[si].forEach((team, rankIdx) => {
        const elo = snap.eloByTeam ? snap.eloByTeam[team] : null;
        const flag = flagByTeam[team] || '';
        const elim = eliminatedAfter[team] > 0 && si > eliminatedAfter[team];
        const hidden = !rankState.showElim && elim;
        const pending = snap.live && snap.pendingTeams && snap.pendingTeams.has(team);

        if (hidden) return;

        const zIndex = isScale ? (numTeams - rankIdx) : 1;
        let topPx;
        if (isScale) {
          topPx = scaleTopPx(elo, rawMin, rawMax, scaleH);
        } else if (!rankState.trueRank) {
          topPx = compactSlot * RANK_ROW_H + (RANK_ROW_H - FLAG_PX_H) / 2;
        } else {
          topPx = rankIdx * RANK_ROW_H + (RANK_ROW_H - FLAG_PX_H) / 2;
        }
        compactSlot++;

        const pin = document.createElement('div');
        pin.className = 'flag-pin';
        pin.dataset.team = team;
        pin.dataset.baseZ = zIndex;
        pin.dataset.tipHtml = buildTipHtml(team, elo, si);
        pin.style.top = topPx + 'px';
        pin.style.zIndex = zIndex;

        const iconStyle = `background-image:url('data/flags/${flag}.svg')` +
          (elim ? ';filter:grayscale(100%);opacity:0.4'
                : pending ? ';filter:grayscale(80%);opacity:0.35' : '');
        const icon = document.createElement('span');
        icon.className = 'icon';
        icon.style.cssText = iconStyle;
        pin.appendChild(icon);

        col.appendChild(pin);
        if (isScale) pinData.push({ el: pin, topPx });
      });

      if (isScale && pinData.length) {
        const STEP = FLAG_PX_W + SCALE_GAP;
        const sorted = [...pinData].sort((a, b) => a.topPx - b.topPx);

        // Pass 1: greedy lane assignment
        const nextFreeY = [-Infinity, -Infinity, -Infinity];
        const laneOf = new Map();
        sorted.forEach(p => {
          let best = -1;
          for (let l = 0; l < 3; l++) {
            if (nextFreeY[l] <= p.topPx) {
              if (best === -1 || nextFreeY[l] > nextFreeY[best]) best = l;
            }
          }
          if (best === -1) best = 1;
          laneOf.set(p, best);
          nextFreeY[best] = p.topPx + FLAG_PX_H;
        });

        // Pass 2: visual centering per transitive cluster
        let gi = 0;
        while (gi < sorted.length) {
          let gj = gi + 1;
          while (gj < sorted.length && sorted[gj].topPx - sorted[gj - 1].topPx < FLAG_PX_H) gj++;
          const group = sorted.slice(gi, gj);
          const lanes = [...new Set(group.map(p => laneOf.get(p)))];
          const spread = (lanes.length - 1) * STEP;
          const laneMinTop = Object.fromEntries(lanes.map(l => [l, Math.min(...group.filter(p => laneOf.get(p) === l).map(p => p.topPx))]));
          const laneOffset = {};
          [...lanes].sort((a, b) => laneMinTop[a] - laneMinTop[b]).forEach((l, k) => { laneOffset[l] = -spread / 2 + k * STEP; });
          group.forEach(p => {
            p.el.style.left = `calc(50% + ${laneOffset[laneOf.get(p)]}px)`;
          });
          gi = gj;
        }
      }

      const debugCb = debugClustersCb;
      if (isScale && debugCb && debugCb.checked && pinData.length) {
        const atOneLess = pinData
          .map(p => ({ el: p.el, topPx: scaleTopPx(snap.eloByTeam[p.el.dataset.team], rawMin, rawMax, scaleH - 1) }))
          .sort((a, b) => a.topPx - b.topPx);
        let lo = 0;
        for (let hi = 0; hi < atOneLess.length; hi++) {
          while (atOneLess[hi].topPx - atOneLess[lo].topPx >= FLAG_PX_H) lo++;
          if (hi - lo + 1 >= 4) {
            const actualTops = atOneLess.slice(lo, hi + 1).map(p => pinData.find(q => q.el === p.el).topPx);
            const top = Math.min(...actualTops);
            const bottom = Math.max(...actualTops) + FLAG_PX_H;
            const box = document.createElement('div');
            box.className = 'debug-cluster';
            box.style.top = (top - 2) + 'px';
            box.style.height = (bottom - top + 4) + 'px';
            col.appendChild(box);
          }
        }
      }
    }

    addGridLines(col);

    if (isScale && scaleHasError && (snap.complete || snap.live) && snap.eloByTeam) {
      const warn = document.createElement('div');
      warn.className = 'scale-error';
      warn.textContent = '⚠ 4+ equal ELOs';
      col.appendChild(warn);
    }

    body.appendChild(col);
  });

}

// ── Rankings hover & info panel ───────────────────────────────────────────

function initRankingsHover() {
  const container = document.getElementById('rankings-cols');
  const infoPanel = document.getElementById('rank-info');
  let activeTeam = null;
  let activateTimer = null;
  let resetTimer = null;

  const updateInfoPosition = () => {
    const gridRect = container.getBoundingClientRect();
    const panelW = infoPanel.offsetWidth;
    const x = Math.max(8, gridRect.left - panelW);
    const panelH = infoPanel.offsetHeight;
    const y = Math.max(8, (window.innerHeight - panelH) / 2);
    infoPanel.style.left = x + 'px';
    infoPanel.style.top = y + 'px';
  };

  const showInfo = pin => {
    infoPanel.innerHTML = pin.dataset.tipHtml || '';
    updateInfoPosition();
    infoPanel.style.visibility = 'visible';
  };

  const hideInfo = () => { infoPanel.style.visibility = 'hidden'; };

  const applyHighlight = team => {
    activeTeam = team;
    container.querySelectorAll('[data-team]').forEach(el => {
      const isHovered = el.dataset.team === team;
      el.style.opacity = isHovered ? '1' : '0.15';
      el.style.zIndex = isHovered ? '9999' : (el.dataset.baseZ || '');
    });
  };

  const applyReset = () => {
    activeTeam = null;
    container.querySelectorAll('[data-team]').forEach(el => {
      el.style.opacity = '';
      el.style.zIndex = el.dataset.baseZ || '';
    });
  };

  const scheduleReset = () => {
    clearTimeout(activateTimer); activateTimer = null;
    if (!resetTimer) resetTimer = setTimeout(() => { resetTimer = null; applyReset(); hideInfo(); }, 300);
  };

  container.addEventListener('mouseover', e => {
    const pin = e.target.closest('[data-team]');
    if (!pin) { scheduleReset(); return; }
    const team = pin.dataset.team;
    clearTimeout(resetTimer); resetTimer = null;
    showInfo(pin);
    if (team === activeTeam) return;
    clearTimeout(activateTimer);
    activateTimer = setTimeout(() => { activateTimer = null; applyHighlight(team); }, 200);
  });

  container.addEventListener('mouseleave', scheduleReset);
}

// ── Page view (Match List ↔ Rankings) ────────────────────────────────────

let currentPageView = null;

function setPageView(view) {
  if (view !== 'matches' && view !== 'rankings') view = 'matches';
  if (view === currentPageView) return;
  currentPageView = view;
  document.getElementById('matches-view').style.display = view === 'matches' ? 'block' : 'none';
  document.getElementById('rankings-view').style.display = view === 'rankings' ? 'block' : 'none';
  document.getElementById('tab-matches').classList.toggle('active', view === 'matches');
  document.getElementById('tab-rankings').classList.toggle('active', view === 'rankings');
  if (view === 'matches') render();
  if (view === 'rankings') renderRankings();
  if (location.hash.slice(1) !== view) history.replaceState(null, '', '#' + view);
}

function validateContract() {
  const required = { teams, GAMES, YEAR, TEAM_ELOS, GAMESETS, CONFEDERATIONS, tbody, thead };
  for (const [k, v] of Object.entries(required)) {
    if (typeof v === 'undefined') throw new Error(`shared.js: page must define "${k}" before loading this script`);
  }
  if (!(tbody instanceof Element)) throw new Error('shared.js: "tbody" must be a DOM element — check that id="games" exists in the page');
  if (!(thead instanceof Element)) throw new Error('shared.js: "thead" must be a DOM element — check that #matches-view thead exists in the page');
  if (!Array.isArray(GAMESETS) || GAMESETS.length < 1 || GAMESETS[0][1] !== 0) {
    throw new Error('GAMESETS must be an array whose first entry has lastGameNumber = 0 (the pre-tournament snapshot)');
  }
  for (let i = 1; i < GAMESETS.length; i++) {
    if (GAMESETS[i][1] <= GAMESETS[i - 1][1]) {
      throw new Error(`GAMESETS[${i}] lastGameNumber (${GAMESETS[i][1]}) must be greater than GAMESETS[${i-1}] (${GAMESETS[i-1][1]})`);
    }
  }
  if (!Array.isArray(CONFEDERATIONS) || CONFEDERATIONS.length === 0) {
    throw new Error('CONFEDERATIONS must be a non-empty array');
  }
  const teamNames = new Set(teams.map(t => t.name));
  for (const g of GAMES) {
    if (!teamNames.has(g.homeTeam)) console.warn(`shared.js: game #${g.gameNumber} homeTeam "${g.homeTeam}" not found in teams — flag and confederation will be missing`);
    if (!teamNames.has(g.awayTeam)) console.warn(`shared.js: game #${g.gameNumber} awayTeam "${g.awayTeam}" not found in teams — flag and confederation will be missing`);
  }
  // Spot-check ELO chain sync: each team's first game pre-ELO must equal TEAM_ELOS,
  // since build.py seeds the chain from there. Catches hand-edits to teamElos that
  // weren't followed by a build.py run, and the most common class of chain bugs.
  if (Object.keys(TEAM_ELOS).length > 0) {
    const firstGameSeen = new Set();
    for (const g of GAMES) {
      if (!firstGameSeen.has(g.homeTeam) && g.homeTeam in TEAM_ELOS) {
        if (g.homeEloPre !== null && g.homeEloPre !== TEAM_ELOS[g.homeTeam]) {
          throw new Error(`shared.js: homeEloPre mismatch for "${g.homeTeam}" in game #${g.gameNumber}: embedded ${g.homeEloPre} ≠ TEAM_ELOS ${TEAM_ELOS[g.homeTeam]} — run scripts/build.py to resync`);
        }
        firstGameSeen.add(g.homeTeam);
      }
      if (!firstGameSeen.has(g.awayTeam) && g.awayTeam in TEAM_ELOS) {
        if (g.awayEloPre !== null && g.awayEloPre !== TEAM_ELOS[g.awayTeam]) {
          throw new Error(`shared.js: awayEloPre mismatch for "${g.awayTeam}" in game #${g.gameNumber}: embedded ${g.awayEloPre} ≠ TEAM_ELOS ${TEAM_ELOS[g.awayTeam]} — run scripts/build.py to resync`);
        }
        firstGameSeen.add(g.awayTeam);
      }
    }
  }
}
validateContract();

window.addEventListener('hashchange', () => setPageView(location.hash.slice(1)));
setPageView(location.hash.slice(1) || 'matches');
initRankingsHover();
