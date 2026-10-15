import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber

DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
DURATION_RE = re.compile(r"^\d{1,3}:\d{2}:\d{2}$")
TIME_RANGE_RE = re.compile(
    r"^\d{1,3}:\d{2}(?::\d{2})?\s*-\s*\d{1,3}:\d{2}(?::\d{2})?$"
)

ROW_TOLERANCE = 2  # points; words this close vertically belong to the same row
COLUMN_MARGIN = 2  # points of slack when assigning a word to a column


def is_grey(word):
    """Clockify prints the project in grey and the description in black."""
    color = word.get("non_stroking_color")

    if not color:
        return False

    if isinstance(color, (int, float)):
        color = (color,)

    return max(color) > 0.15


def group_rows(words):
    """Group words into visual rows, each sorted left to right."""
    rows = []

    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(word["top"] - rows[-1][0]) <= ROW_TOLERANCE:
            rows[-1][1].append(word)
        else:
            rows.append([word["top"], [word]])

    return [sorted(row, key=lambda w: w["x0"]) for _, row in rows]


def column_anchors(row):
    """Read the x positions of the Date / Description / Duration / User columns
    off an entry's first row, so the parser does not depend on the report
    language or on where the text happens to wrap."""
    if len(row) < 2:
        return None

    durations = [w for w in row[1:] if DURATION_RE.match(w["text"])]
    if not durations:
        return None

    duration = durations[-1]
    after = [w for w in row if w["x0"] > duration["x0"]]

    return {
        "description": row[1]["x0"],
        "duration": duration["x0"],
        "user": after[0]["x0"] if after else float("inf"),
    }


def split_columns(row, anchors):
    """Return the row's text split into date / description / duration / user."""
    columns = {"date": [], "description": [], "duration": [], "user": []}

    for word in row:
        x0 = word["x0"]

        if x0 < anchors["description"] - COLUMN_MARGIN:
            name = "date"
        elif x0 < anchors["duration"] - COLUMN_MARGIN:
            name = "description"
        elif x0 < anchors["user"] - COLUMN_MARGIN:
            name = "duration"
        else:
            name = "user"

        columns[name].append(word)

    return columns


def parse_block(rows):
    """Turn the rows belonging to one time entry into a record."""
    anchors = column_anchors(rows[0])
    if anchors is None:
        return None

    date = ""
    duration = ""
    time_range = ""
    description_rows = []
    project_rows = []
    user_parts = []

    for row in rows:
        columns = split_columns(row, anchors)

        if columns["date"]:
            date = " ".join(w["text"] for w in columns["date"])

        if columns["description"]:
            text = " ".join(w["text"] for w in columns["description"])
            target = project_rows if is_grey(columns["description"][0]) else description_rows
            target.append(text)

        if columns["duration"]:
            text = " ".join(w["text"] for w in columns["duration"])

            if TIME_RANGE_RE.match(text):
                time_range = text
            elif DURATION_RE.match(text):
                duration = text

        if columns["user"]:
            user_parts.append(" ".join(w["text"] for w in columns["user"]))

    # Fallback for reports where the project is not printed in grey: it is
    # always the last line of the description column.
    if not project_rows and len(description_rows) > 1:
        project_rows = [description_rows.pop()]

    return {
        "Date": date,
        "Description": " ".join(description_rows),
        "Project": " ".join(project_rows),
        "Duration": duration,
        "Time Range": time_range,
        "User": " ".join(user_parts),
    }


def extract(pdf_file):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            words = page.extract_words(extra_attrs=["non_stroking_color"])

            block = []

            for row in group_rows(words):
                starts_entry = DATE_RE.match(row[0]["text"]) is not None

                if starts_entry:
                    if block:
                        rows.append(block)
                    block = [row]
                    continue

                if not block:
                    continue

                # A continuation row always starts flush with one of the entry's
                # columns; anything else (page footers, totals) ends the entry.
                anchors = column_anchors(block[0])
                if anchors and not any(
                    abs(row[0]["x0"] - anchors[name]) <= COLUMN_MARGIN
                    for name in ("description", "duration", "user")
                ):
                    rows.append(block)
                    block = []
                    continue

                block.append(row)

            if block:
                rows.append(block)

    records = [record for block in rows if (record := parse_block(block))]

    return pd.DataFrame(
        records,
        columns=["Date", "Description", "Project", "Duration", "Time Range", "User"],
    )


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
