import streamlit as st
import pandas as pd
import zipfile
import io
import os
import shutil
from copy import copy
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell

st.set_page_config(page_title="Traffic Sheet Automation", layout="wide")
st.title("Traffic Sheet Automation Dashboard")

MASTER_TEMPLATE_PATH = "master_template.xlsm"

prisma_file = st.file_uploader(
    "Upload Prisma / Tsheet Export",
    type=["xlsx", "xlsm", "xls", "csv"]
)

creative_type = st.radio(
    "Creative setup type",
    ["Single creative per ad", "Multiple creatives per ad"]
)

creative_uploads = st.file_uploader(
    "Upload Creative ZIP or Individual Creative Files",
    type=["zip", "jpg", "jpeg", "png", "gif", "html", "htm", "mp4", "webp"],
    accept_multiple_files=True
)

ad_name_option = st.radio(
    "Is Ad Name same as Placement Name?",
    ["Yes", "No"]
)

ad_name_format = None
if ad_name_option == "No":
    ad_name_format = st.selectbox(
        "Select Ad Name format",
        [
            "Last 3 parts from Placement Name",
            "Last 4 parts from Placement Name",
            "Client_Platform_Audience_Dimension",
            "Client_Audience_Dimension",
            "Platform_Audience_Dimension",
            "Audience_Dimension"
        ]
    )

custom_1x1 = st.text_input("1x1 Creative Name", value="Tracking 1x1")

st.subheader("Paste UTM Data")
utm_text = st.text_area(
    "Paste UTM data from Excel. Recommended columns: Placement Name, Dimension, UTM",
    height=150
)

utm_output_column = st.text_input(
    "Traffic_Doc UTM output column",
    value="P"
)


def read_prisma_file(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()

    if ext == "csv":
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file, sheet_name=0)


def read_utm_text(text):
    if not text.strip():
        return pd.DataFrame()

    try:
        return pd.read_csv(io.StringIO(text), sep="\t")
    except Exception:
        try:
            return pd.read_csv(io.StringIO(text))
        except Exception:
            return pd.DataFrame()


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
                        names.append(os.path.basename(file_name))
        else:
            names.append(uploaded_file.name)

    return names


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).lower().strip()


def normalize_dimension(value):
    if pd.isna(value):
        return ""
    return (
        str(value)
        .lower()
        .replace(" ", "")
        .replace("*", "x")
        .replace("×", "x")
    )


def split_placement(name):
    if pd.isna(name):
        return []

    name = str(name).strip()

    if "_" in name:
        return [x for x in name.split("_") if x]

    if "-" in name:
        return [x for x in name.split("-") if x]

    return [name]


def generate_ad_name(placement_name, dimension, selected_format):
    parts = split_placement(placement_name)
    dim = str(dimension).strip()

    if selected_format == "Last 3 parts from Placement Name":
        return "_".join(parts[-3:]) if len(parts) >= 3 else str(placement_name)

    if selected_format == "Last 4 parts from Placement Name":
        return "_".join(parts[-4:]) if len(parts) >= 4 else str(placement_name)

    client = parts[0] if len(parts) > 0 else ""
    platform = parts[1] if len(parts) > 1 else ""
    audience = parts[-2] if len(parts) >= 2 else ""

    if selected_format == "Client_Platform_Audience_Dimension":
        return "_".join([client, platform, audience, dim])

    if selected_format == "Client_Audience_Dimension":
        return "_".join([client, audience, dim])

    if selected_format == "Platform_Audience_Dimension":
        return "_".join([platform, audience, dim])

    if selected_format == "Audience_Dimension":
        return "_".join([audience, dim])

    return str(placement_name)


def match_creatives(dimension, placement_name, creative_names):
    dim = normalize_dimension(dimension)
    placement_parts = split_placement(placement_name)
    results = []

    for creative in creative_names:
        clean_creative = normalize_text(creative).replace(" ", "").replace("*", "x")
        score = 0

        if dim and dim in clean_creative:
            score += 10

        for part in placement_parts:
            clean_part = normalize_text(part)
            if len(clean_part) >= 3 and clean_part in clean_creative:
                score += 1

        if score >= 10:
            results.append((creative, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in results]


def find_utm_for_row(utm_df, placement_name, dimension):
    if utm_df.empty:
        return ""

    df = utm_df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]

    placement_col = None
    dimension_col = None
    utm_col = None

    for col in df.columns:
        if "placement" in col:
            placement_col = col
        if "dimension" in col or "size" in col:
            dimension_col = col
        if "utm" in col or "url" in col or "click" in col:
            utm_col = col

    if not utm_col:
        return ""

    placement_clean = normalize_text(placement_name)
    dim_clean = normalize_dimension(dimension)

    for _, row in df.iterrows():
        row_placement = normalize_text(row.get(placement_col, "")) if placement_col else ""
        row_dimension = normalize_dimension(row.get(dimension_col, "")) if dimension_col else ""

        placement_match = (
            placement_clean
            and row_placement
            and (placement_clean in row_placement or row_placement in placement_clean)
        )

        dimension_match = True
        if dimension_col:
            dimension_match = dim_clean == row_dimension

        if placement_match and dimension_match:
            return row.get(utm_col, "")

    return ""


def clear_prisma_sheet_only(ws):
    for row in ws.iter_rows():
        for cell in row:
            if not isinstance(cell, MergedCell):
                cell.value = None


def paste_dataframe_to_prisma(ws, df):
    clear_prisma_sheet_only(ws)

    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        if not isinstance(cell, MergedCell):
            cell.value = col_name

    for row_idx, row in enumerate(df.itertuples(index=False), start=2):
        for col_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            if not isinstance(cell, MergedCell):
                cell.value = "" if pd.isna(value) else value


def clear_multi_sheet(ws):
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if not isinstance(cell, MergedCell):
                cell.value = None


if st.button("Generate Traffic Sheet"):

    if not os.path.exists(MASTER_TEMPLATE_PATH):
        st.error("master_template.xlsm not found. Keep it in the same folder as app.py.")
        st.stop()

    if prisma_file is None:
        st.error("Please upload Prisma / Tsheet export.")
        st.stop()

    prisma_df = read_prisma_file(prisma_file)
    utm_df = read_utm_text(utm_text)
    creative_names = extract_creative_names(creative_uploads)

    template_bytes = io.BytesIO()
    with open(MASTER_TEMPLATE_PATH, "rb") as f:
        template_bytes.write(f.read())
    template_bytes.seek(0)

    wb = load_workbook(template_bytes, keep_vba=True)

    ws_prisma = wb["Prisma Export - Paste as values"]
    ws_traffic = wb["Traffic_Doc"]
    ws_multi = wb["Multi-Ad or Creative Rotation"]

    # Only Prisma paste tab is cleared.
    paste_dataframe_to_prisma(ws_prisma, prisma_df)

    # Traffic_Doc is NOT cleared. Formulas remain as-is.
    # Only Multi-Ad output rows are cleared.
    clear_multi_sheet(ws_multi)

    multi_row = 2
    review_rows = []

    for i, row in prisma_df.iterrows():
        excel_row = i + 7   # Traffic_Doc starts from row 7 in your template

        try:
            dimension = row.iloc[19]        # Prisma T
            placement_name = row.iloc[20]   # Prisma U
            start_date = row.iloc[22]       # Prisma W
            end_date = row.iloc[23]         # Prisma X
        except IndexError:
            st.error("Tsheet needs columns up to X.")
            st.stop()

        if ad_name_option == "Yes":
            ad_name = placement_name
        else:
            ad_name = generate_ad_name(placement_name, dimension, ad_name_format)

        # Only manual editable columns
        ws_traffic[f"H{excel_row}"] = ad_name

        matched_utm = find_utm_for_row(utm_df, placement_name, dimension)
        if matched_utm:
            ws_traffic[f"{utm_output_column}{excel_row}"] = matched_utm

        dim_clean = normalize_dimension(dimension)

        if dim_clean == "1x1":
            ws_traffic[f"K{excel_row}"] = custom_1x1
            continue

        if creative_names:
            matches = match_creatives(dimension, placement_name, creative_names)

            if creative_type == "Single creative per ad":
                if len(matches) >= 1:
                    ws_traffic[f"K{excel_row}"] = matches[0]
                else:
                    ws_traffic[f"K{excel_row}"] = "Creative not found"
                    review_rows.append({
                        "Traffic_Doc Row": excel_row,
                        "Placement Name": placement_name,
                        "Dimension": dimension,
                        "Issue": "Creative not found"
                    })

            else:
                if len(matches) == 1:
                    ws_traffic[f"K{excel_row}"] = matches[0]

                elif len(matches) > 1:
                    ws_traffic[f"K{excel_row}"] = "Multiple creatives - see rotation tab"

                    for creative in matches:
                        ws_multi[f"A{multi_row}"] = ad_name
                        ws_multi[f"D{multi_row}"] = creative
                        ws_multi[f"F{multi_row}"] = "Even"
                        ws_multi[f"G{multi_row}"] = start_date
                        ws_multi[f"H{multi_row}"] = end_date
                        multi_row += 1
                else:
                    ws_traffic[f"K{excel_row}"] = "Creative not found"
                    review_rows.append({
                        "Traffic_Doc Row": excel_row,
                        "Placement Name": placement_name,
                        "Dimension": dimension,
                        "Issue": "Creative not found"
                    })

    final_output = io.BytesIO()
    wb.save(final_output)
    final_output.seek(0)

    st.success("Traffic Sheet generated successfully.")

    if creative_names:
        st.subheader("Creative Files Found")
        st.write(creative_names)

    if review_rows:
        st.warning("Some rows need manual review.")
        st.dataframe(pd.DataFrame(review_rows), use_container_width=True)

    st.download_button(
        label="Download Final Traffic Sheet",
        data=final_output,
        file_name="Final_Traffic_Sheet.xlsm",
        mime="application/vnd.ms-excel.sheet.macroEnabled.12"
    )