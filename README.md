# Clockify PDF Extractor

Extracts time entries from a **Clockify Detailed Report (PDF)** and converts them into an Excel spreadsheet (`.xlsx`).

> **Important:** This tool only supports the **Detailed Report** PDF exported from Clockify. Other report types (such as Summary, Weekly, or custom exports) are not supported and may produce incorrect results.

## Requirements

* Python 3.9+
* Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage

Convert a Clockify PDF to an Excel file with the same name:

```bash
python clockify_pdf_extractor.py report.pdf
```

Example:

```bash
python clockify_pdf_extractor.py "Clockify Detailed Report.pdf"
```

This generates:

```text
Clockify Detailed Report.xlsx
```

### Specify an output file

Provide a custom output filename using `-o` or `--output`:

```bash
python clockify_pdf_extractor.py report.pdf -o timesheet.xlsx
```

or

```bash
python clockify_pdf_extractor.py report.pdf --output timesheet.xlsx
```

## Output

The generated Excel file contains the following columns:

| Column      | Description                    |
| ----------- | ------------------------------ |
| Date        | Entry date                     |
| Description | Task description               |
| Project     | Clockify project               |
| Duration    | Time spent on the task         |
| Time Range  | Start and end time             |
| User        | User associated with the entry |

## Example

```text
$ py .\clockify_pdf_extractor.py .\sample\Clockify_Time_Report_Detailed_01_07_2026-31_07_2026.pdf

         Date Description Project  Duration           Time Range          User
0  23/07/2026     Task-04    TEST  04:00:00  15:00:00 - 19:00:00  Lucas Picchi
1  22/07/2026     Task-04    TEST  04:00:00  13:00:00 - 17:00:00  Lucas Picchi
2  16/07/2026     Task-03    TEST  04:00:00  13:00:00 - 17:00:00  Lucas Picchi
3  15/07/2026     Task-03    TEST  04:00:00  16:00:00 - 20:00:00  Lucas Picchi
4  14/07/2026     Task-02    TEST  04:00:00  13:00:00 - 17:00:00  Lucas Picchi
5  10/07/2026     Task-02    TEST  04:00:00  13:00:00 - 17:00:00  Lucas Picchi
6  09/07/2026     Task-02    TEST  04:00:00  10:00:00 - 14:00:00  Lucas Picchi
7  07/07/2026     Task-01    TEST  04:00:00  15:15:00 - 19:15:00  Lucas Picchi
8  02/07/2026     Task-01    TEST  04:00:00  10:00:00 - 14:00:00  Lucas Picchi

Extracted 9 entries.
Saved to sample\Clockify_Time_Report_Detailed_01_07_2026-31_07_2026.xlsx
```

## Notes

* Works with reports exported in any language. Columns are located by their position on the page, not by matching header text, so a Spanish `Informe detallado` parses the same as an English `Detailed report`.
* Handles descriptions long enough to wrap onto several lines, which push the project and time range onto lines of their own.
* Automatically ignores report headers, totals, footers, and other non-entry lines.
* If `--output` is omitted, the Excel file is created next to the PDF with the same base filename.

