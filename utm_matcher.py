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

def find_utm_for_row(utm_df, placement_name, dimension):
    if utm_df is None or utm_df.empty:
        return ""

    df = utm_df.copy()
    cols = list(df.columns)

    placement_col = find_col(cols, ["placement"])
    dimension_col = find_col(cols, ["dimension", "size"])
    utm_col = find_col(cols, ["utm", "url", "click", "landing"])

    if not utm_col:
        return ""

    placement_clean = normalize_text(placement_name)
    dim_clean = normalize_dimension(dimension)

    best_score = -1
    best_utm = ""

    for _, r in df.iterrows():
        row_placement = normalize_text(r.get(placement_col, "")) if placement_col else ""
        row_dimension = normalize_dimension(r.get(dimension_col, "")) if dimension_col else ""

        score = 0

        if placement_clean and row_placement:
            if placement_clean == row_placement:
                score += 100
            elif placement_clean in row_placement or row_placement in placement_clean:
                score += 80

        if dimension_col:
            if dim_clean and row_dimension and dim_clean == row_dimension:
                score += 20
            elif dim_clean and row_dimension:
                score -= 10

        if score > best_score:
            best_score = score
            best_utm = r.get(utm_col, "")

    return best_utm if best_score >= 80 else ""
