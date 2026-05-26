import pandas as pd

def keyword_filter(df: pd.DataFrame, keyword: str, columns: list[str]) -> pd.DataFrame:
    if not keyword:
        return df
    key = keyword.lower()
    mask = False
    for col in columns:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.lower().str.contains(key, na=False)
    return df[mask]
