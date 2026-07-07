import re
import pandas as pd

DEFAULT_RULE = "Placement Name = Ad Name"

STATE_MAP = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "IA": "Iowa", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts",
    "MD": "Maryland", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota",
    "MO": "Missouri", "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina",
    "ND": "North Dakota", "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NV": "Nevada", "NY": "New York", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VA": "Virginia", "VT": "Vermont", "WA": "Washington",
    "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming",
}

def load_account_taxonomy(path="Account_Taxonomy_Master.xlsx"):
    try:
        df = pd.read_excel(path)
        df = df.dropna(subset=["Account", "Rule"])
        return dict(zip(df["Account"].astype(str), df["Rule"].astype(str)))
    except Exception:
        return {
            "Simon": DEFAULT_RULE,
            "Best Friends Animal Society": DEFAULT_RULE,
            "BFAS": DEFAULT_RULE,
            "ConEd": DEFAULT_RULE,
            "HMH": DEFAULT_RULE,
            "Ascensus": DEFAULT_RULE,
            "IMC": DEFAULT_RULE,
            "Tillamook": DEFAULT_RULE,
            "AAA": DEFAULT_RULE,
            "Hyatt": DEFAULT_RULE,
            "Famous Footwear": DEFAULT_RULE,
            "Fossil": DEFAULT_RULE,
            "Lenovo": DEFAULT_RULE,
            "UPS Store": "Creative Name = Ad Name",
            "USTA": "Dimension = Ad Name",
            "Pulte": "Pulte: Market_Brand_Initiative_Property_Duration",
            "Touchstone Energy": "Last Meaningful Placement Segment",
            "Anthem / Elevance": "ELV_LOB_State_Channel_SizeOrDuration",
        }

def load_state_map(path="State_Master.xlsx"):
    try:
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]
        return dict(zip(df["State Code"].astype(str).str.upper(), df["State Name"].astype(str)))
    except Exception:
        return STATE_MAP

def split_placement(name):
    if pd.isna(name):
        return []
    name = str(name).strip()
    if "_" in name:
        return [x.strip() for x in name.split("_") if x.strip()]
    if "-" in name:
        return [x.strip() for x in name.split("-") if x.strip()]
    return [name]

def duration_from_text(text):
    s = str(text).lower()
    if ":30" in s or "30sec" in s or "30s" in s:
        return "30Sec"
    if ":15" in s or "15sec" in s or "15s" in s:
        return "15Sec"
    if ":06" in s or ":6" in s or "6sec" in s or "06sec" in s:
        return "6Sec"
    return ""

def generate_pulte_ad_name(placement_name):
    parts = split_placement(placement_name)
    duration = duration_from_text(placement_name)

    if "VIID" in parts:
        idx = parts.index("VIID")
        if len(parts) > idx + 4:
            return f"{parts[idx+1]}_{parts[idx+2]}_{parts[idx+3]}_{parts[idx+4]}_{duration}".strip("_")

    # fallback: find duration and take last useful business segments
    useful = [p for p in parts if p.upper() not in {"NAN", "VIDEO", "BANNER"} and not p.isdigit()]
    return "_".join(useful[-4:] + ([duration] if duration else []))

def generate_touchstone_ad_name(placement_name):
    parts = split_placement(placement_name)
    ignore = {
        "TEC", "TEC2023", "PGR", "VID", "NAN", "Trade Desk", "GM", "Spot X PMP",
        "dCPM", "CTV", ":15", ":30", ":06", "Third Party"
    }
    meaningful = [p.strip() for p in parts if p.strip() and p.strip() not in ignore]
    return meaningful[-1] if meaningful else str(placement_name)

def generate_elv_ad_name(placement_name, dimension, state_map=None):
    state_map = state_map or STATE_MAP
    parts = split_placement(placement_name)
    text = str(placement_name).lower()

    lob = ""
    state_name = ""
    channel = ""
    size_or_duration = ""

    for p in parts:
        upper = p.upper().strip()
        if upper in ["MDCD", "MDCR", "CSBD", "BRAN"]:
            lob = upper
        if upper in state_map:
            state_name = state_map[upper]

    if "display" in text or "banner" in text:
        channel = "Display"
        size_or_duration = str(dimension).strip()
    elif "ctv" in text:
        channel = "CTV"
        size_or_duration = duration_from_text(placement_name) or str(dimension).strip()
    elif "olv" in text or "video" in text:
        channel = "OLV"
        size_or_duration = duration_from_text(placement_name) or str(dimension).strip()
    elif "audio" in text:
        channel = "Audio"
        size_or_duration = duration_from_text(placement_name) or str(dimension).strip()

    return "_".join([x for x in ["ELV", lob, state_name, channel, size_or_duration] if x])

def generate_ad_name(placement_name, dimension, account, rule, matched_creative="", state_map=None):
    if rule == "Placement Name = Ad Name":
        return str(placement_name)

    if rule == "Creative Name = Ad Name":
        return matched_creative or ""

    if rule == "Dimension = Ad Name":
        return str(dimension)

    if rule == "Pulte: Market_Brand_Initiative_Property_Duration":
        return generate_pulte_ad_name(placement_name)

    if rule == "Last Meaningful Placement Segment":
        return generate_touchstone_ad_name(placement_name)

    if rule == "ELV_LOB_State_Channel_SizeOrDuration":
        return generate_elv_ad_name(placement_name, dimension, state_map)

    return str(placement_name)
