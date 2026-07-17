import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber

DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}")
DURATION_RE = re.compile(r"(\d{2}:\d{2}:\d{2})")
TIME_RANGE_RE = re.compile(r"(\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2})")


def extract(pdf_file):
    lines = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.splitlines():
                line = line.strip()

                if (
                    not line
                    or line.startswith("Detailed report")
                    or line.startswith("Date Description")
                    or line.startswith("Total:")
                    or line.startswith("01/03/2026 -")
                    or "Created with Clockify" in line
                    or line == "32:00:00"
                ):
                    continue

                lines.append(line)

    rows = []
    i = 0

    while i < len(lines):

        line1 = lines[i]

        if not DATE_RE.match(line1):
            i += 1
            continue

        if i + 1 >= len(lines):
            break

        line2 = lines[i + 1]

        date = line1[:10]

        duration_match = list(DURATION_RE.finditer(line1))
        if not duration_match:
            i += 2
            continue

        duration = duration_match[-1].group(1)

        before_duration = line1[10:duration_match[-1].start()].strip()

        user = line1[duration_match[-1].end():].strip()

        time_match = TIME_RANGE_RE.search(line2)
        if not time_match:
            i += 2
            continue

        project = line2[:time_match.start()].strip()
        time_range = time_match.group(1)

        rows.append(
            {
                "Date": date,
                "Description": before_duration,
                "Project": project,
                "Duration": duration,
                "Time Range": time_range,
                "User": user,
            }
        )

        i += 2

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("-o", "--output")

    args = parser.parse_args()

    pdf = Path(args.pdf)
    output = Path(args.output) if args.output else pdf.with_suffix(".xlsx")

    df = extract(pdf)
    df.to_excel(output, index=False)

    print(df)
    print(f"\nExtracted {len(df)} entries.")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()