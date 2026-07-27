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
import os
import re
from typing import Dict, List, Tuple


PULTE_VIP_SITE_MAPPING = {
    "realtor": ["realtor", "realtor native"],
    "zillow": ["zillow", "zillow native"],
}


def clean_filename(filename: str) -> str:
    """
    Removes folder path and file extension.
    """

    filename = os.path.basename(str(filename).strip())

    return os.path.splitext(filename)[0]


def normalize_match_text(value: str) -> str:
    """
    Converts separators and punctuation into spaces.

    Example:
    Sage_Run -> sage run
    Sage-Run -> sage run
    """

    value = clean_filename(value).lower()

    value = re.sub(r"[_\-]+", " ", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def extract_pulte_vip_placement_details(
    placement_name: str,
    fallback_dimension: str = "",
) -> Dict[str, str]:
    placement_name = str(placement_name or "").strip()

    result = {
        "community": "",
        "site": "",
        "image_token": "",
        "dimension": "",
        "community_id": "",
    }

    if not placement_name:
        return result

    placement_lower = placement_name.lower()

    if "realtor" in placement_lower:
        result["site"] = "realtor"
    elif "zillow" in placement_lower:
        result["site"] = "zillow"

    dimension_match = re.search(
        r"(?<!\d)(\d{2,4}\s*[xX]\s*\d{2,4})(?!\d)",
        placement_name,
    )

    if dimension_match:
        result["dimension"] = (
            dimension_match.group(1)
            .replace(" ", "")
            .lower()
        )
    else:
        fallback_match = re.search(
            r"(?<!\d)(\d{2,4}\s*[xX]\s*\d{2,4})(?!\d)",
            str(fallback_dimension),
        )

        if fallback_match:
            result["dimension"] = (
                fallback_match.group(1)
                .replace(" ", "")
                .lower()
            )

    community_id_match = re.search(
        r"_(\d{5,7})(?:_|$)",
        placement_name,
    )

    if community_id_match:
        result["community_id"] = community_id_match.group(1)

    conversion_match = re.search(
        r"_Conversion_([^_]+)_(.+)",
        placement_name,
        flags=re.IGNORECASE,
    )

    if conversion_match:
        result["image_token"] = conversion_match.group(1).upper()

        parts_after_image = [
            part.strip()
            for part in conversion_match.group(2).split("_")
            if part.strip()
        ]

        community_id_index = None

        for index, part in enumerate(parts_after_image):
            if re.fullmatch(r"\d{5,7}", part):
                community_id_index = index
                break

        if community_id_index is not None and community_id_index > 0:
            result["community"] = parts_after_image[
                community_id_index - 1
            ]

    return result


def score_pulte_vip_creative(
    creative_filename: str,
    placement_name: str,
    fallback_dimension: str = "",
) -> Tuple[int, List[str]]:
    """
    Scores one creative against one Pulte VIP placement.

    Priority:
    1. Community
    2. Site
    3. Dimension
    4. Image token
    """

    details = extract_pulte_vip_placement_details(
        placement_name,
        fallback_dimension,
    )

    creative_text = normalize_match_text(creative_filename)

    score = 0
    reasons = []

    community_text = normalize_match_text(details["community"])

    if community_text:
        if community_text in creative_text:
            score += 100
            reasons.append("community")
        else:
            # A creative should not match a different community.
            return -1, ["community mismatch"]

    site = details["site"]

    if site:
        site_terms = PULTE_VIP_SITE_MAPPING.get(site, [site])

        if any(
            normalize_match_text(term) in creative_text
            for term in site_terms
        ):
            score += 50
            reasons.append("site")
        else:
            # Prevent Zillow creatives going to Realtor placements.
            return -1, ["site mismatch"]

    dimension = details["dimension"]

    if dimension:
        normalized_dimension = dimension.lower().replace(" ", "")

        creative_compact = creative_text.replace(" ", "")

        if normalized_dimension in creative_compact:
            score += 30
            reasons.append("dimension")
        else:
            return -1, ["dimension mismatch"]

    image_token = details["image_token"]

    if image_token:
        if image_token.lower() in creative_text:
            score += 20
            reasons.append("image")
        else:
            return -1, ["image mismatch"]

    return score, reasons


def match_pulte_vip_creatives(
    creative_filenames: List[str],
    placement_name: str,
    fallback_dimension: str = "",
) -> List[str]:
    """
    Returns all best matching creatives for a Pulte VIP placement.
    """

    scored_creatives = []

    for creative_filename in creative_filenames:
        score, reasons = score_pulte_vip_creative(
            creative_filename=creative_filename,
            placement_name=placement_name,
            fallback_dimension=fallback_dimension,
        )

        if score >= 0:
            scored_creatives.append(
                {
                    "filename": creative_filename,
                    "score": score,
                    "reasons": reasons,
                }
            )

    if not scored_creatives:
        return []

    best_score = max(item["score"] for item in scored_creatives)

    return [
        item["filename"]
        for item in scored_creatives
        if item["score"] == best_score
    ]
