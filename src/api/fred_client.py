import requests
import pandas as pd
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FredClient:
    """
    Client for extracting data from Federal Reserve Economic Data (FRED) API.
    Supports Data Fetching AND Release Calendar Scheduling.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"

    def get_series_data(
        self, series_id: str, start_date: Optional[str] = None, units: str = "lin"
    ) -> pd.DataFrame:
        """Fetches observations (Historical Data)."""
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "units": units,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            observations = data.get("observations", [])

            if not observations:
                return pd.DataFrame()

            df = pd.DataFrame(observations)
            df = df[["date", "value"]]
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])

            return df.dropna()

        except Exception as e:
            logger.error(f"Data Request failed for {series_id}: {e}")
            return pd.DataFrame()

    def get_next_release(self, series_id: str) -> str:
        """
        Chains two API calls to find the confirmed Next Release Date.
        1. Find the Release ID for the series.
        2. Query the Release Calendar for future dates.
        """
        try:
            # Step 1: Get Release ID
            rel_url = f"{self.base_url}/series/release"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
            }

            resp = requests.get(rel_url, params=params, timeout=5)
            resp.raise_for_status()
            releases = resp.json().get("releases", [])

            if not releases:
                return "Unknown"

            release_id = releases[0]["id"]

            # Step 2: Get Future Dates
            dates_url = f"{self.base_url}/release/dates"
            params = {
                "release_id": release_id,
                "api_key": self.api_key,
                "file_type": "json",
                "include_release_dates_with_no_data": "true",  # Crucial for future dates
                "realtime_start": datetime.now().strftime("%Y-%m-%d"),
            }

            resp = requests.get(dates_url, params=params, timeout=5)
            dates_data = resp.json().get("release_dates", [])

            # Filter for dates >= Today
            today = datetime.now().strftime("%Y-%m-%d")
            future_dates = [d["date"] for d in dates_data if d["date"] >= today]

            if future_dates:
                return sorted(future_dates)[0]  # Return the earliest future date
            else:
                return "Pending Schedule"

        except Exception as e:
            logger.warning(f"Calendar fetch failed for {series_id}: {e}")
            return "Estimate Only"
