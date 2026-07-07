import os
import zipfile
import pandas as pd

def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()

def normalize_dimension(value):
    if pd.isna(value):
        return ""
    return (
        str(value).lower()
        .replace(" ", "")
        .replace("*", "x")
        .replace("×", "x")
    )

def split_placement(name):
    if pd.isna(name):
        return []
    name = str(name).strip()
    if "_" in name:
        return [x.strip() for x in name.split("_") if x.strip()]
    if "-" in name:
        return [x.strip() for x in name.split("-") if x.strip()]
    return [name]

def extract_creative_names(files):
    names = []
    if not files:
        return names

    for uploaded_file in files:
        ext = uploaded_file.name.split(".")[-1].lower()

        if ext == "zip":
            with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                for file_name in zip_ref.namelist():
                    if not file_name.endswith("/"):
                        base = os.path.basename(file_name)
                        if base:
                            names.append(base)
        else:
            names.append(uploaded_file.name)

    return sorted(set(names))

def match_creatives(dimension, placement_name, creative_names):
    dim = normalize_dimension(dimension)
    placement_parts = split_placement(placement_name)
    results = []

    for creative in creative_names:
        clean_creative = normalize_text(creative).replace(" ", "").replace("*", "x").replace("×", "x")
        score = 0

        if dim and dim in clean_creative:
            score += 100

        # video durations
        placement_text = normalize_text(placement_name)
        if (":30" in placement_text or "30sec" in placement_text) and ("30" in clean_creative):
            score += 80
        if (":15" in placement_text or "15sec" in placement_text) and ("15" in clean_creative):
            score += 80
        if (":06" in placement_text or "6sec" in placement_text) and ("06" in clean_creative or "6" in clean_creative):
            score += 80

        for part in placement_parts:
            clean_part = normalize_text(part)
            if len(clean_part) >= 4 and clean_part in clean_creative:
                score += 5

        if score >= 80:
            results.append((creative, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in results]
