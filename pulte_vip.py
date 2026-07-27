import re
import os
from openpyxl import load_workbook
def load_tracking_codes():
    def parse_pulte_vip_placement(placement_name):
    """
    Parses a real Pulte VIP Prisma placement name.

    Example:
    Direct_Display_Native_Realtor_Prospect_Geo_DMA_
    2nd Party Data_CPM_Cross Device_1200x800_SS_Local_
    Conversion_EXTD_West Florida_Pulte_Heavy Up_
    Caldera_211086_TAM FL_Onsite
    """

    if not placement_name:
        return {}

    parts = [
        part.strip()
        for part in str(placement_name).split("_")
        if part.strip()
    ]

    data = {
        "source": "",
        "dimension": "",
        "image": "",
        "division": "",
        "builder": "",
        "campaign": "",
        "community": "",
        "community_id": "",
        "region": "",
        "placement_type": ""
    }

    # Find source
    for part in parts:
        if part.lower() in {"realtor", "zillow"}:
            data["source"] = part
            break

    # Find creative dimension
    for part in parts:
        if re.fullmatch(r"\d{2,4}[xX]\d{2,4}", part):
            data["dimension"] = part.lower().replace("x", "x")
            break

    # Find community ID
    for index, part in enumerate(parts):
        if re.fullmatch(r"\d{5,7}", part):
            data["community_id"] = part

            # Community is immediately before Community ID
            if index >= 1:
                data["community"] = parts[index - 1]

            # Region is immediately after Community ID
            if index + 1 < len(parts):
                data["region"] = parts[index + 1]

            # Placement type is after Region
            if index + 2 < len(parts):
                data["placement_type"] = parts[index + 2]

            # Campaign, Builder, Division and Image are before Community
            if index >= 2:
                data["campaign"] = parts[index - 2]

            if index >= 3:
                data["builder"] = parts[index - 3]

            if index >= 4:
                data["division"] = parts[index - 4]

            if index >= 5:
                data["image"] = parts[index - 5]

            break

    return data
    """
    Reads all Adobe tracking lookup values from
    Pulte_Adobe_Tracking_Codes.xlsm
    """

    file_path = os.path.join(
        os.path.dirname(__file__),
        "Pulte_Adobe_Tracking_Codes.xlsm"
    )

    wb = load_workbook(file_path, data_only=True)

    ws = wb["ChannelTrackingValues"]

    lookup = {
        "Medium": {},
        "Source": {},
        "Division": {},
        "Region": {},
        "Content": {},
        "Campaign": {},
        "Vendor": {},
        "Image": {}
    }

    columns = {
        "Medium": (1, 2),
        "Source": (3, 4),
        "Division": (5, 6),
        "Region": (7, 8),
        "Content": (9, 10),
        "Campaign": (11, 12),
        "Vendor": (13, 14),
        "Image": (15, 16)
    }

    for category, (name_col, code_col) in columns.items():

        for row in range(5, ws.max_row + 1):

            name = ws.cell(row=row, column=name_col).value
            code = ws.cell(row=row, column=code_col).value

            if not name or not code:
                continue

            lookup[category][str(name).strip().lower()] = str(code).strip()

    return lookup
