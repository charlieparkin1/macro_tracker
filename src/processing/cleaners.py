import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalise_series(df: pd.DataFrame, source: str, indicator: str) -> pd.DataFrame:
    """
    Standardises a DataFrame from any API into the project's universal schema.
    Ref: sample_data_shapes.txt

    Schema: [date, value, indicator, source]

    Args:
        df: Raw DataFrame from an API client.
        source: Name of the data source (e.g., 'FRED', 'ECB').
        indicator: Name of the economic indicator (e.g., 'US_CPI').

    Returns:
        pd.DataFrame: A cleaned, sorted DataFrame adhering to the schema.
    """
    # 1. Safety Check: Handle empty inputs (e.g., from failed API calls)
    if df.empty:
        logger.warning(f"Received empty DataFrame for {indicator} ({source})")
        return pd.DataFrame(columns=["date", "value", "indicator", "source"])

    # 2. Copy to avoid SettingWithCopy warnings
    clean_df = df.copy()

    # 3. Standardise Column Names
    # We expect raw DFs to have 'date' and 'value'.
    # If uppercase (DATE, VALUE), we lower them.
    clean_df.columns = [c.lower() for c in clean_df.columns]

    required_cols = {"date", "value"}
    if not required_cols.issubset(clean_df.columns):
        logger.error(f"Data missing required columns. Found: {clean_df.columns}")
        return pd.DataFrame()

    # 4. Type Enforcement
    # Ensure date is actually datetime
    clean_df["date"] = pd.to_datetime(clean_df["date"], errors="coerce")

    # Ensure value is numeric (remove any non-numeric chars if they exist)
    clean_df["value"] = pd.to_numeric(clean_df["value"], errors="coerce")

    # Drop rows where date or value failed conversion
    clean_df = clean_df.dropna(subset=["date", "value"])

    # 5. Add Metadata
    clean_df["source"] = source
    clean_df["indicator"] = indicator

    # 6. Final Polish
    # Sort by date ascending
    clean_df = clean_df.sort_values(by="date", ascending=True)

    # Reorder columns
    clean_df = clean_df[["date", "value", "indicator", "source"]]

    return clean_df


# Quick Test Block
if __name__ == "__main__":
    # Simulate some "Messy" Data to prove it works
    data = {
        "DATE": ["2023-01-01", "2023-02-01", "bad-date"],
        "Value": ["3.4", 3.1, "5.0"],
    }
    raw_df = pd.DataFrame(data)

    print("--- Input Raw DF (Messy) ---")
    print(raw_df)

    print("\n--- Output Clean DF (Standardised) ---")
    processed = normalise_series(raw_df, "FRED", "US_CPI")
    print(processed)
