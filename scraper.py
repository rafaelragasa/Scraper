import csv, re, glob, os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def process_file(path):
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Total Usage
    total = 459.0
    p_tags = soup.find_all("p")

    for i, p in enumerate(p_tags):
        if "Total Data Usage" in p.text:
            try:
                total = float(
                    p_tags[i + 1].text.replace("GB", "").strip()
                )
            except:
                pass

    # Bar Heights
    bars = soup.find_all(
        "rect",
        class_="MuiBarElement-series-y_0"
    )

    heights = [
        float(b.get("height", 0))
        for b in bars
    ]

    if not heights:
        return None, None

    gb_per_pixel = total / sum(heights)

    # Active Month
    months = {
        m: i for i, m in enumerate(
            ["Jan","Feb","Mar","Apr","May","Jun",
             "Jul","Aug","Sep","Oct","Nov","Dec"], 1)
    }

    active = soup.select_one('h6[class*="1bcwr2w"]')
    month_num = months.get(
        active.text.strip() if active else "",
        datetime.now().month
    )

    # Extract Year
    year = datetime.now().year

    for p in p_tags:
        match = re.search(r'\d{1,2}/\d{1,2}/(\d{4})', p.text)

        if match:
            year = int(match.group(1))
            break

    start = datetime(year, month_num, 17)

    rows = [
        {
            "Date": (start + timedelta(days=i)).strftime("%m/%d/%Y"),
            "GB": round(h * gb_per_pixel, 2)
        }
        for i, h in enumerate(heights)
    ]

    return total, rows


def auto_scrape_starlink():

    base = os.path.dirname(os.path.abspath(__file__))

    files = glob.glob(os.path.join(base, "*.html"))

    if not files:
        print("No HTML files found.")
        return

    print("\nHTML Files:")

    for i, f in enumerate(files, 1):
        print(f"[{i}] {os.path.basename(f)}")

    print("[0] Process ALL")

    choice = input("\nSelect: ")

    try:
        selected = files if choice == "0" else [files[int(choice)-1]]
    except:
        print("Invalid choice.")
        return

    all_data = {}
    grand_total = 0

    for file in selected:

        print(f"\nProcessing {os.path.basename(file)}")

        total, rows = process_file(file)

        if not rows:
            continue

        grand_total += total

        for r in rows:
            all_data[r["Date"]] = (
                all_data.get(r["Date"], 0) + r["GB"]
            )

    output = os.path.join(base, "data_usage.csv")

    with open(output, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["Date", "Data Usage (GB)"])

        for date in sorted(
            all_data,
            key=lambda d: datetime.strptime(d, "%m/%d/%Y")
        ):
            writer.writerow([date, round(all_data[date], 2)])

        writer.writerow([])
        writer.writerow(["Total Usage", round(grand_total, 2)])

    print(f"\nSaved: {output}")
    print(f"Grand Total: {round(grand_total, 2)} GB")


if __name__ == "__main__":
    auto_scrape_starlink()
