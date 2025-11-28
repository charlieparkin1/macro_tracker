import requests
import pandas as pd
import logging
from typing import Optional

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EcbClient:
    """
    Client for extracting data from the European Central Bank (ECB) Data Portal.
    Ref: https://data.ecb.europa.eu/help/api/overview
    """

    def __init__(self):
        # UPDATED: New Base URL for ECB Data Portal (Old 'sdw-wsrest' is deprecated)
        self.base_url = "https://data-api.ecb.europa.eu/service/data"

    def get_series_data(self, flow_ref: str, key: str) -> pd.DataFrame:
        print(f"--- DEBUG: Requesting {flow_ref}/{key} ---")

        url = f"{self.base_url}/{flow_ref}/{key}"
        # 'dataonly' and 'jsondata' are still valid parameters for the new API
        params = {"detail": "dataonly", "format": "jsondata"}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return self._parse_sdmx_response(response.json())

        except Exception as e:
            print(f"--- DEBUG: API Error: {e} ---")
            return pd.DataFrame()

    def _parse_sdmx_response(self, data: dict) -> pd.DataFrame:
        try:
            # 1. Extract Values
            data_sets = data.get("dataSets", [])
            if not data_sets:
                return pd.DataFrame()

            series_dict = data_sets[0].get("series", {})
            if not series_dict:
                return pd.DataFrame()

            obs_dict = list(series_dict.values())[0].get("observations", {})

            # 2. Extract Dates
            structure = data.get("structure", {})
            dimensions = structure.get("dimensions", {}).get("observation", [])
            time_dim = next(
                (d for d in dimensions if d.get("id") == "TIME_PERIOD"), None
            )

            if not time_dim:
                return pd.DataFrame()

            dates = [item["id"] for item in time_dim.get("values", [])]

            # 3. Zip together
            rows = []
            for i, date_str in enumerate(dates):
                idx_str = str(i)
                if idx_str in obs_dict:
                    val = obs_dict[idx_str][0]
                    rows.append({"date": date_str, "value": val})

            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"])

            return df

        except Exception as e:
            print(f"--- DEBUG: Parsing Error: {e} ---")
            return pd.DataFrame()


if __name__ == "__main__":
    print("--- DEBUG: Entering Test Block ---")
    client = EcbClient()

    # Test: Eurozone HICP (Inflation)
    print("Fetching Eurozone Inflation...")
    df = client.get_series_data("ICP", "M.U2.N.000000.4.ANR")

    print("\n--- RESULTS ---")
    print(df.tail())
