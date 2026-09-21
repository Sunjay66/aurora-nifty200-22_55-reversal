async function loadScannerData() {
  const response = await fetch("data/latest_results.json?ts=" + Date.now(), { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load scanner data.");
  return response.json();
}

function fmtNumber(value) {
  if (value === null || value === undefined || value === "") return "—";
  return Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function setText(id, value) {
  document.getElementById(id).textContent = value ?? "—";
}

function render(data) {
  setText("marketStatus", data.market_status);
  setText("marketDataDate", data.market_data_date_display);
  setText("dataFetchedAt", data.data_fetched_at_display);
  setText("pageRefreshedAt", data.page_refreshed_at_display);
  setText("universe", data.universe);
  setText("candidateCount", data.candidate_count);

  document.getElementById("statusBadge").textContent =
    data.market_status === "OPEN" ? "● DAILY DATA CURRENT" : "● MARKET CLOSED — LAST TRADING DATA";

  setText(
    "lastRunNote",
    `Latest market-data session: ${data.market_data_date_display}. Page generated from the stored scan result.`
  );

  const body = document.getElementById("candidateBody");
  body.innerHTML = "";

  if (!data.candidates || data.candidates.length === 0) {
    document.getElementById("emptyState").hidden = false;
    return;
  }
  document.getElementById("emptyState").hidden = true;

  for (const row of data.candidates) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.stock}</td>
      <td>${row.cross_date}</td>
      <td>${row.sessions_since_cross}</td>
      <td>${fmtNumber(row.cmp)}</td>
      <td>${fmtNumber(row.ema22)}</td>
      <td>${fmtNumber(row.ema55)}</td>
      <td>${fmtNumber(row.ema150)}</td>
      <td>${fmtNumber(row.ema200)}</td>
      <td>${row.macd_status}</td>
      <td>${row.rvol}</td>
      <td>${row.reversal_candle}</td>
    `;
    body.appendChild(tr);
  }
}

loadScannerData()
  .then(render)
  .catch(err => {
    document.getElementById("statusBadge").textContent = "DATA LOAD ERROR";
    document.getElementById("lastRunNote").textContent = err.message;
  });
