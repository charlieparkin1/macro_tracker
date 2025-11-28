import time
import schedule
import pandas as pd
import logging
import os
from datetime import datetime, timedelta

# SECURITY FIX: Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.api.fred_client import FredClient
from src.api.ecb_client import EcbClient
from src.processing.cleaners import normalise_series
from src.processing.event_detector import EventDetector
from src.alerts.terminal_alerts import print_event_alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MacroScheduler")


class MacroScheduler:
    def __init__(self):
        # SECURITY FIX: Only load from environment. No hardcoded fallback.
        api_key = os.getenv("FRED_API_KEY")
        
        if not api_key:
            logger.warning("⚠️  No FRED API Key found! Please check your .env file or deployment secrets.")
            # We pass a placeholder so the code doesn't crash immediately, 
            # but API calls will fail gracefully later.
            api_key = "MISSING_KEY"

        self.fred = FredClient(api_key=api_key)
        self.ecb = EcbClient()
        self.detector = EventDetector(lookback_window=12)
        self.last_seen_dates = {}

        self.portfolio = [
            {"id": "CPIAUCSL", "source": "FRED", "name": "US CPI", "units": "pc1"},
            {"id": "PPIFIS", "source": "FRED", "name": "US PPI", "units": "pc1"},
            {"id": "PAYEMS", "source": "FRED", "name": "US NFP", "units": "chg"},
            {
                "id": "UNRATE",
                "source": "FRED",
                "name": "US Unemployment",
                "units": "lin",
            },
            {
                "id": "CPALTT01GBM659N",
                "source": "FRED",
                "name": "UK Inflation",
                "units": "lin",
            },
            {
                "id": "ICP/M.U2.N.000000.4.ANR",
                "source": "ECB",
                "name": "Eurozone Inflation",
                "units": "lin",
            },
        ]

        os.makedirs("data/processed", exist_ok=True)

    def run_pipeline(self):
        logger.info(
            f"--- Running Update Cycle: {datetime.now().strftime('%H:%M:%S')} ---"
        )

        # 1. Update Data Series
        for item in self.portfolio:
            try:
                self.process_indicator(item)
            except Exception as e:
                logger.error(f"Failed to process {item['name']}: {e}")

        # 2. Update Calendar (New Feature)
        self.update_calendar()

    def process_indicator(self, item):
        df = pd.DataFrame()
        if item["source"] == "FRED":
            units = item.get("units", "lin")
            df = self.fred.get_series_data(item["id"], units=units)
        elif item["source"] == "ECB":
            parts = item["id"].split("/")
            df = self.ecb.get_series_data(parts[0], parts[1])

        clean_df = normalise_series(df, item["source"], item["name"])
        if clean_df.empty:
            return

        filename = (
            item["name"].replace(" ", "_").replace("(", "").replace(")", "").lower()
            + ".csv"
        )
        filepath = os.path.join("data/processed", filename)
        clean_df.to_csv(filepath, index=False)

        latest_date = clean_df.iloc[-1]["date"]
        indicator_id = item["name"]

        if indicator_id not in self.last_seen_dates:
            self.last_seen_dates[indicator_id] = latest_date
            logger.info(f"Initialized {indicator_id}")
            return

        if latest_date > self.last_seen_dates[indicator_id]:
            analysis = self.detector.analyze_release(clean_df)
            print_event_alert(analysis)
            self.last_seen_dates[indicator_id] = latest_date

    def update_calendar(self):
        """Generates a verified calendar.csv using API data."""
        # Check if we have a valid key before trying to fetch calendar data
        if self.fred.api_key == "MISSING_KEY":
            logger.warning("Skipping calendar update due to missing API key.")
            return

        logger.info("Updating Release Calendar...")
        calendar_rows = []

        for item in self.portfolio:
            next_date = "N/A"

            # FRED: Fetch real calendar date
            if item["source"] == "FRED":
                next_date = self.fred.get_next_release(item["id"])

            # ECB: Fallback to heuristic (API doesn't allow easy calendar lookup)
            else:
                # Estimate: Last known date + 30 days
                # Ideally, we would switch Eurozone to FRED to fix this properly
                next_date = "Estimate (TBD)"

            calendar_rows.append(
                {
                    "Indicator": item["name"],
                    "Source": item["source"],
                    "Next Release": next_date,
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            )

        cal_df = pd.DataFrame(calendar_rows)
        cal_df.to_csv("data/processed/calendar.csv", index=False)

    def start(self):
        logger.info("Macro Tracker Engine Started. Press Ctrl+C to stop.")
        self.run_pipeline()
        schedule.every(1).minutes.do(self.run_pipeline)
        while True:
            schedule.run_pending()
            time.sleep(1)