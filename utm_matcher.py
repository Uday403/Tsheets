import io
import pandas as pd
from creative_matcher import normalize_dimension, normalize_text


def read_utm_text(text):
    if not text or not text.strip():
        return pd.DataFrame()

    try:
        return pd.read_csv(io.StringIO(text), sep="\t")
    except Exception:
        try:
            return pd.read_csv(io.StringIO(text))
        except Exception:
            return pd.DataFrame()


def find_col(columns, keywords):
    for col in columns:
        c = str(col).lower().strip()
        if any(k in c for k in keywords):
            return col
    return None


def find_utm_for_row(utm_df, placement_name, dimension, ad_name=""):
    if utm_df is None or utm_df.empty:
        return ""

    # If only one UTM is pasted, apply it to every row
    if len(utm_df) == 1:
        for col in utm_df.columns:
            if any(x in str(col).lower() for x in ["utm", "url", "click", "landing"]):
                return utm_df.iloc[0][col]

        return utm_df.iloc[0].dropna().astype(str).iloc[-1]

    df = utm_df.copy()
    cols = list(df.columns)

    placement_col = find_col(cols, ["placement", "name", "ad"])
    dimension_col = find_col(cols, ["dimension", "size"])
    utm_col = find_col(cols, ["utm", "url", "click", "landing"])

    if not utm_col:
        utm_col = cols[-1]

    placement_text = f"{placement_name} {ad_name}".lower()
    dim_clean = normalize_dimension(dimension)

    best_score = -1
    best_utm = ""

    for _, r in df.iterrows():

        row_text = ""
        if placement_col:
            row_text = normalize_text(r.get(placement_col, ""))

        row_dim = ""
        if dimension_col:
            row_dim = normalize_dimension(r.get(dimension_col, ""))

        score = 0

        for word in row_text.replace("_", " ").replace("-", " ").split():
            if len(word) >= 4 and word in placement_text:
                score += 10

        if dim_clean and row_dim and dim_clean == row_dim:
            score += 50

        if score > best_score:
            best_score = score
            best_utm = r.get(utm_col, "")

    return best_utm if best_score >= 10 else ""
