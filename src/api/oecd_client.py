import pandas as pd
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OecdClient:
    """
    STUBBED CLIENT: OECD API is currently blocking requests (403).
    Kept in codebase to maintain project structure.
    """

    def __init__(self):
        self.base_url = "STUBBED"

    def get_series_data(
        self, dataset_id: str, filter_expression: str, start_year: Optional[int] = None
    ) -> pd.DataFrame:
        # Silently return empty DataFrame so the pipeline continues
        logger.warning("OECD Client is disabled. Returning empty data.")
        return pd.DataFrame(columns=["date", "value"])


if __name__ == "__main__":
    print("OECD Client is in Safe Mode (Stubbed).")
