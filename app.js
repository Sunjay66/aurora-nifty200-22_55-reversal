const DATA_URL = "data/latest_results.json";

function setText(id, value, fallback = "—") {
    const element = document.getElementById(id);

    if (!element) {
        return;
    }

    if (value === undefined || value === null || value === "") {
        element.textContent = fallback;
    } else {
        element.textContent = value;
    }
}

function fmtNumber(value) {
    if (value === undefined || value === null || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function fmtRvol(value) {
    if (value === undefined || value === null || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toFixed(2) + "x";
}

function render(data) {

    // -----------------------------
    // Header / metadata
    // -----------------------------

    setText(
        "marketStatus",
        data.market_status
    );

    setText(
        "marketDataDate",
        data.market_data_session_display ||
        data.market_data_date
    );

    setText(
        "dataFetchedAt",
        data.data_fetched_display
    );

    setText(
        "pageRefreshedAt",
        data.page_refreshed_display
    );

    setText(
        "universe",
        data.universe,
        "Nifty 200"
    );

    setText(
        "candidateCount",
        data.candidate_count,
        "0"
    );


    // -----------------------------
    // Status badge
    // -----------------------------

    const statusBadge =
        document.getElementById("statusBadge");

    if (statusBadge) {

        const status =
            data.market_status || "";

        if (status.includes("TODAY'S DATA")) {

            statusBadge.textContent =
                "● MARKET CLOSED — TODAY'S DATA";

        } else if (
            status.includes("LAST TRADING DATA")
        ) {

            statusBadge.textContent =
                "● MARKET CLOSED — LAST TRADING DATA";

        } else if (
            status === "OPEN"
        ) {

            statusBadge.textContent =
                "● DAILY DATA CURRENT";

        } else {

            statusBadge.textContent =
                "● " + status;
        }
    }


    // -----------------------------
    // Latest market-data session
    // -----------------------------

    setText(
        "lastRunNote",
        `Latest market-data session: ${
            data.market_data_session_display ||
            data.market_data_date ||
            "—"
        }. Page generated from the stored scan result.`
    );


    // -----------------------------
    // Candidate table
    // -----------------------------

    const body =
        document.getElementById("candidateBody");

    const emptyState =
        document.getElementById("emptyState");

    if (!body) {
        return;
    }

    body.innerHTML = "";

    const candidates =
        Array.isArray(data.candidates)
            ? data.candidates
            : [];


    if (candidates.length === 0) {

        if (emptyState) {
            emptyState.hidden = false;
        }

        return;
    }


    if (emptyState) {
        emptyState.hidden = true;
    }


    for (const row of candidates) {

        const tr =
            document.createElement("tr");

        tr.innerHTML = `
            <td><strong>${row.stock ?? "—"}</strong></td>

            <td>${row.cross_date ?? "—"}</td>

            <td>${row.sessions_since_cross ?? "—"}</td>

            <td>${fmtNumber(row.cmp)}</td>

            <td>${fmtNumber(row.ema22)}</td>

            <td>${fmtNumber(row.ema55)}</td>

            <td>${fmtNumber(row.ema150)}</td>

            <td>${fmtNumber(row.ema200)}</td>

            <td>${row.macd_status ?? "—"}</td>

            <td>${fmtRvol(row.rvol)}</td>

            <td>${row.candle ?? "None"}</td>
        `;

        body.appendChild(tr);
    }
}


// -----------------------------
// Load latest scanner data
// -----------------------------

async function loadScannerData() {

    const response =
        await fetch(
            DATA_URL + "?ts=" + Date.now(),
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            "Could not load scanner data."
        );
    }

    return response.json();
}


loadScannerData()

    .then(render)

    .catch(error => {

        console.error(
            "Aurora scanner error:",
            error
        );

        const statusBadge =
            document.getElementById(
                "statusBadge"
            );

        if (statusBadge) {

            statusBadge.textContent =
                "DATA LOAD ERROR";
        }

        setText(
            "lastRunNote",
            error.message
        );
    });
