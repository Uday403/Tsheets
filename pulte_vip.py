import os
from openpyxl import load_workbook
def load_tracking_codes():
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
