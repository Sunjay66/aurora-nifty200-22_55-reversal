const DATA_URL = "./data/latest_results.json";

function $(id) {
    return document.getElementById(id);
}

function safe(value, fallback = "—") {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }
    return value;
}

function formatNumber(value, decimals = 2) {
    if (value === undefined || value === null || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatRvol(value) {
    if (value === undefined || value === null || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return number.toFixed(2) + "x";
}

function setText(id, value, fallback = "—") {
    const element = $(id);

    if (element) {
        element.textContent = safe(value, fallback);
    }
}

function renderCandidates(data) {

    const candidates = Array.isArray(data.candidates)
        ? data.candidates
        : [];

    setText(
        "marketStatus",
        data.market_status,
        "UNKNOWN"
    );

    setText(
        "marketDataDate",
        data.market_data_session_display ||
        data.market_data_date,
        "—"
    );

    setText(
        "dataFetched",
        data.data_fetched_display,
        "—"
    );

    setText(
        "pageRefreshed",
        data.page_refreshed_display,
        "—"
    );

    setText(
        "universe",
        data.universe,
        "Nifty 200"
    );

    setText(
        "candidateCount",
        candidates.length,
        "0"
    );

    const sessionElement = $("latestSession");

    if (sessionElement) {

        const sessionText =
            data.market_data_session_display ||
            data.market_data_date ||
            "—";

        sessionElement.textContent =
            `Latest market-data session: ${sessionText}. Page generated from the stored scan result.`;
    }

    const tableBody = $("candidateTableBody");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = "";

    if (candidates.length === 0) {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td colspan="12" class="empty-state">
                No Nifty 200 candidates currently satisfy all mandatory rules.
            </td>
        `;

        tableBody.appendChild(row);

        return;
    }

    candidates.forEach(candidate => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>
                <strong>${safe(candidate.stock)}</strong>
            </td>

            <td>
                ${safe(candidate.cross_date)}
            </td>

            <td>
                ${safe(candidate.sessions_since_cross)}
            </td>

            <td>
                ${formatNumber(candidate.cmp)}
            </td>

            <td>
                ${formatNumber(candidate.ema22)}
            </td>

            <td>
                ${formatNumber(candidate.ema55)}
            </td>

            <td>
                ${formatNumber(candidate.ema150)}
            </td>

            <td>
                ${formatNumber(candidate.ema200)}
            </td>

            <td>
                ${safe(candidate.macd_status)}
            </td>

            <td>
                ${formatRvol(candidate.rvol)}
            </td>

            <td>
                ${safe(candidate.candle)}
            </td>
        `;

        tableBody.appendChild(row);
    });
}

async function loadScannerData() {

    try {

        const response = await fetch(
            `${DATA_URL}?t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data = await response.json();

        renderCandidates(data);

    } catch (error) {

        console.error(
            "Aurora scanner data error:",
            error
        );

        const tableBody = $("candidateTableBody");

        if (tableBody) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="12" class="empty-state">
                        Unable to load the latest scanner data.
                    </td>
                </tr>
            `;
        }
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadScannerData
);
