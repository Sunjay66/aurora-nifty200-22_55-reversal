# Aurora Nifty 200 — Daily 22/55 Trend Reversal

Separate GitHub Pages project for the Aurora Nifty 200 daily scanner.

## Mandatory candidate rules

1. 22 EMA crossed above 55 EMA within 1–3 completed sessions.
2. Current price is above 22, 55, 150 and 200 EMA.
3. 150 EMA is above 200 EMA.

MACD, RVOL and reversal-candle information are displayed only. They are not filters.

## Timestamp design

The site deliberately keeps three timestamps:

- **Market data date:** the latest actual trading session represented by the daily data.
- **Data fetched:** when the automation retrieved the market data.
- **Page refreshed:** when the result page data was generated/published.

If the market is closed for a weekend or holiday, the market-data date remains the most recent trading session. The automation may still refresh the page.

## Current repository contents

`index.html` — web page  
`style.css` — page styling  
`app.js` — reads the latest JSON result  
`data/latest_results.json` — current scan result  
`.github/workflows/` — automation will be added here

The JSON currently contains the validated Colab candidates as sample data. The live automation should replace it with fresh results.
