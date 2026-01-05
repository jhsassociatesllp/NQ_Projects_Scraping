from playwright.sync_api import sync_playwright
import re
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv 

load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def clean_text(text: str) -> str:
    """Normalize whitespace"""
    return re.sub(r"\s+", " ", text).strip()

# def save_to_mongodb(data: list):
#     if not data:
#         print("⚠️ No data to insert")
#         return

#     mongo_uri = os.getenv("MONGO_URI")  # mongodb+srv://...
#     db_name = "Timesheets"

#     client = MongoClient(mongo_uri)
#     db = client[db_name]
#     collection = db["Projects"]

#     inserted = 0
#     skipped = 0

#     for row in data:
#         doc = {
#             "project_code": row["Project Code"],
#             "project_name": row["Project Name"],

#             "client_code": row["Client Code"],
#             "client_name": row["Client Name"],

#             "partner_emp_code": row["Project Partner Emp Code"],
#             "partner_name": row["Project Partner Name"],

#             "manager_emp_code": row["Project Manager Emp Code"],
#             "manager_name": row["Project Manager Name"],

#             "priority": row["Priority"],
#             "created_on": row["Created On"],

#             "created_by_emp_code": row["Created By Emp Code"],
#             "created_by_name": row["Created By Name"],

#             "updated_on": row["Updated On"],
#         }

#         try:
#             collection.insert_one(doc)
#             inserted += 1
#         except DuplicateKeyError:
#             skipped += 1

#     client.close()

#     print(f"✅ MongoDB insert complete → Inserted: {inserted}, Skipped: {skipped}")

def save_to_mongodb(data: list):
    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    db = client["Timesheets"]
    collection = db["Projects"]

    inserted = 0
    skipped = 0

    for row in data:
        project_code = row["Project Code"]

        exists = collection.find_one(
            {"project_code": project_code},
            {"_id": 1}
        )

        if exists:
            skipped += 1
            continue

        collection.insert_one({
            "project_code": project_code,
            "project_name": row["Project Name"],
            "client_code": row["Client Code"],
            "client_name": row["Client Name"],
            "partner_emp_code": row["Project Partner Emp Code"],
            "partner_name": row["Project Partner Name"],
            "manager_emp_code": row["Project Manager Emp Code"],
            "manager_name": row["Project Manager Name"],
            "priority": row["Priority"],
            "created_on": row["Created On"],
            "created_by_emp_code": row["Created By Emp Code"],
            "created_by_name": row["Created By Name"],
            "updated_on": row["Updated On"],
        })

        inserted += 1

    client.close()
    print(f"✅ MongoDB → Inserted: {inserted}, Skipped: {skipped}")


def save_to_excel(data: list, output_path: str):
    if not data:
        raise ValueError("No data to write to Excel")

    df = pd.DataFrame(data)

    # Normalize base columns first
    df['Client Name'] = df['Client Code'].str.split('-').str[1].str.strip()
    df['Client Code'] = df['Client Code'].str.split('-').str[0].str.strip()

    df['Project Partner Name'] = df['Project Partner'].str.split('-').str[1].str.strip()
    df['Project Partner Emp Code'] = df['Project Partner'].str.split('-').str[0].str.strip()

    df['Project Manager Name'] = df['Project Manager / Team Lead'].str.split('-').str[1].str.strip()
    df['Project Manager Emp Code'] = df['Project Manager / Team Lead'].str.split('-').str[0].str.strip()

    df['Created By Name'] = df['Created By'].str.split('-').str[1].str.strip()
    df['Created By Emp Code'] = df['Created By'].str.split('-').str[0].str.strip()

    # ✅ FINAL ORDER (single source of truth)
    final_columns = [
        "Project Code",
        "Project Name",

        "Client Code",
        "Client Name",

        "Project Partner Emp Code",
        "Project Partner Name",

        "Project Manager Emp Code",
        "Project Manager Name",

        "Priority",
        "Created On",

        "Created By Emp Code",
        "Created By Name",

        "Updated On",
    ]

    df = df[final_columns]

    # df.to_excel(output_path, index=False, engine="openpyxl")

    # print(f"📁 Excel saved successfully → {output_path}")
    save_to_mongodb(df.to_dict("records"))


def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=30)
        context = browser.new_context()
        page = context.new_page()

        # ================= LOGIN =================
        page.goto(LOGIN_URL, timeout=60000)
        page.fill("#email", EMAIL)
        page.fill("#password", PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        # ================= NAVIGATION =================
        page.wait_for_timeout(5000)
        page.click("#switch_to_control_panel")
        page.wait_for_timeout(2000)
        page.click("button.swal2-confirm")
        page.wait_for_timeout(3000)
        page.click("a[href='https://nexusquant.in/PMS/project-list']")
        page.wait_for_timeout(8000)

        # ================= SET PAGINATION = ALL =================
        page.select_option("#dt-length-0", value="-1")
        page.wait_for_timeout(5000)

        # ================= EXTRACT COLUMN HEADERS =================
        header_spans = page.locator(
            "div.dt-scroll-head table.dataTable thead tr th div.dt-column-header span.dt-column-title"
        )

        column_names = [
            clean_text(header_spans.nth(i).inner_text())
            for i in range(header_spans.count())
        ]

        print("COLUMNS:")
        print(column_names)

        # ================= EXTRACT ROW DATA =================
        rows = page.locator(
            "div.dt-scroll-body table#projectTable tbody tr"
        )

        all_data = []

        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator("td")

            row_data = {
                "Project Code": clean_text(cells.nth(0).inner_text()),
                "Project Name": clean_text(cells.nth(1).inner_text()),
                "Client Code": clean_text(cells.nth(2).inner_text()),

                "Project Partner": clean_text(
                    cells.nth(3).locator("div.partner").inner_text()
                ),

                "Project Manager / Team Lead": clean_text(
                    cells.nth(4).locator("div.partner").inner_text()
                ),

                "Priority": clean_text(
                    cells.nth(5).locator("span").inner_text()
                ),

                "Created On": clean_text(cells.nth(6).inner_text()),

                "Created By": clean_text(
                    cells.nth(7).locator("div.partner").inner_text()
                ),

                "Updated On": clean_text(cells.nth(8).inner_text()),
            }

            all_data.append(row_data)

        print(f"\n✅ Extracted {len(all_data)} rows")

        # Example: print first row
        print("\nSample Row:")
        print(all_data[0])

        browser.close()
        output_file = r"D:\vasu\JHS Projects\Nexus Quant\Download Projects data\projects_data.xlsx"

        save_to_excel(all_data, output_file)
        # save_to_mongodb(pd.DataFrame(all_data).to_dict("records"))
        
        return all_data


if __name__ == "__main__":
    data = run_bot()
