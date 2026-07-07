# Tsheet Automation Dashboard

Files included:
- Tsheet.py: Streamlit dashboard
- account_rules.py: Account-specific Ad Name rules
- creative_matcher.py: Creative file extraction and matching
- utm_matcher.py: UTM matching logic
- excel_writer.py: Excel writing helpers
- Account_Taxonomy_Master.xlsx: Account to Ad Name rule mapping
- State_Master.xlsx: State code to state name mapping
- Account_Config.xlsx: Future account-level configuration
- requirements.txt: Streamlit dependencies
- master_template.xlsm: Add your own master template file in GitHub

Important:
- Keep `master_template.xlsm` in the same folder as `Tsheet.py`
- Traffic_Doc formulas are preserved
- Output starts at Traffic_Doc row 9
