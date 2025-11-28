import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventDetector:
    """
    Applies logic to detect macro surprises and classify events.
    Ref: event_detection_logic.txt
    """

    def __init__(self, lookback_window: int = 12):
        # Lookback window for calculating Standard Deviation (e.g., last 12 months)
        self.lookback_window = lookback_window

    def analyze_release(
        self, current_data: pd.DataFrame, consensus_value: float = None
    ) -> Dict[str, Any]:
        """
        Analyzes a new data point against history to determine surprise.
        """
        if current_data.empty or len(current_data) < self.lookback_window:
            return {"status": "insufficient_history"}

        # Sort by date to ensure we get the latest
        df = current_data.sort_values(by="date", ascending=True)

        # Latest actual release
        latest = df.iloc[-1]
        actual_value = latest["value"]

        # 1. Determine "Consensus"
        # If no analyst consensus is provided, use the 3-month moving average
        if consensus_value is None:
            expected_value = df["value"].iloc[-self.lookback_window : -1].mean()
        else:
            expected_value = consensus_value

        # 2. Calculate Deviation (Surprise)
        surprise = actual_value - expected_value

        # 3. Calculate Standard Deviation (Volatility)
        recent_history = df["value"].iloc[-self.lookback_window : -1]
        std_dev = recent_history.std()

        # Avoid division by zero
        if std_dev == 0:
            z_score = 0
        else:
            z_score = surprise / std_dev

        # 4. Classification Logic (Ref: event_detection_logic.txt)
        classification = "Neutral"

        if z_score > 1.0:
            classification = "Large Positive Surprise"
        elif z_score < -1.0:
            classification = "Large Negative Surprise"
        elif 0.3 <= abs(z_score) <= 1.0:
            classification = "Moderate Surprise"

        result = {
            "date": str(latest["date"].date()),
            "indicator": latest.get("indicator", "Unknown"),
            "actual": round(actual_value, 2),
            "expected": round(expected_value, 2),
            "surprise": round(surprise, 3),
            "z_score": round(z_score, 2),
            "classification": classification,
        }

        return result


if __name__ == "__main__":
    # Test Data: History has slight noise (normal market), then a BIG jump
    # History (11 items): varies between 2.9 and 3.1
    history = [3.0, 3.1, 2.9, 3.0, 3.05, 2.95, 3.0, 3.1, 2.9, 3.0, 3.0]
    # Latest Release: Jumps to 3.8
    values = history + [3.8]

    dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")

    df = pd.DataFrame({"date": dates, "value": values})
    df["indicator"] = "TEST_CPI"

    detector = EventDetector()
    print("--- Event Analysis Result ---")
    # We expect a Consensus of ~3.0 based on the average of history
    result = detector.analyze_release(df, consensus_value=3.0)

    # Pretty print the dictionary
    import json

    print(json.dumps(result, indent=2))
