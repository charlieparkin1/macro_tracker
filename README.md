# Real-Time Macro Event Tracker & Analytics Engine

## Project Overview
This application is a specialized **ETL (Extract, Transform, Load) pipeline** designed to monitor, normalize, and analyze high-frequency macroeconomic data in real-time.

Built to mirror the data engineering workflows used in institutional research, the system aggregates live data from major central bank APIs (FRED, ECB), standardizes it into a universal schema, and applies statistical logic to detect market-moving events. It features an interactive **Streamlit dashboard** that provides traders and analysts with immediate visibility into "consensus surprises" and their correlation with asset prices (S&P 500, Yields, FX).

## Key Capabilities
* **Multi-Source Ingestion:** Robust API clients handling disparate data shapes from the **Federal Reserve (FRED)** and **European Central Bank (ECB)**.
* **Market Correlation Engine:** Integrated `yfinance` overlays to visualize real-time relationships between Macro Surprises and asset classes (e.g., *US CPI vs 10Y Treasury Yields*) using dual-axis plotting.
* **Smart Scaling & Outlier Logic:** Proprietary visualization engine that automatically clips statistical outliers (e.g., COVID-19 NFP shocks) to preserve the legibility of monthly fluctuations using quantile analysis.
* **Release Calendar Integration:** Chains API calls to verify official future release dates directly from source exchanges.
* **Resilient Scheduling:** A background orchestration engine (`scheduler.py`) that manages API polling intervals, state persistence, and error logging.

## Technical Architecture
The system follows a modular Service-Oriented Architecture (SOA):
1.  **Ingestion Layer:** Type-safe API clients with retry logic and timeout handling.
2.  **Processing Layer:** Pandas-based transformation engine for cleaning (`cleaners.py`) and statistical analysis (`event_detector.py`).
3.  **Persistence Layer:** Local CSV storage for audit trails and historical backtesting.
4.  **Presentation Layer:** Streamlit frontend with Plotly integration for dynamic charting, dual-axis correlation analysis, and interactive timelines.

## Logic and Methodology
The "Surprise Index" is calculated using a rolling lookback window (default: 12 months) to determine the standard deviation of the indicator.

$$Z = \frac{Actual - Expected}{\sigma_{rolling}}$$

*Where 'Expected' is derived from consensus estimates or statistical forecasting.*

## Installation and Usage

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/macro-tracker.git](https://github.com/yourusername/macro-tracker.git)
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Engine (Backend)**
    ```bash
    python3 main.py
    ```

4.  **Launch the Dashboard (Frontend)**
    ```bash
    streamlit run src/dashboard/main_dashboard.py
    ```

---
*Developed by Charlie Parkin as a portfolio demonstration of financial data engineering.*