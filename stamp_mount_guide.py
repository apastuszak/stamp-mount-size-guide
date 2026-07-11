#!/usr/bin/env python3
"""Figure out which stamp mount size to use for each stamp in a collection.

Usage:
    python stamp_mount_guide.py input.csv [-o output_prefix]

Input file (.csv, .xls/.xlsx/.xlsm, .ods, or .numbers) columns, with or without a header row:
    name, catalog_number, width_mm, height_mm
Output: <output_prefix>.md, <output_prefix>.csv, and <output_prefix>.bbcode.txt (default prefix: stamp_mounts)

Reading .xlsx/.xlsm/.ods files requires pandas, openpyxl, and odfpy:
    pip install pandas openpyxl odfpy
Reading legacy .xls files additionally requires xlrd:
    pip install xlrd
Reading .numbers files requires numbers-parser:
    pip install numbers-parser
"""

import argparse
import csv
import os
import sys

SPREADSHEET_EXTENSIONS = (".xlsx", ".xlsm", ".xls", ".ods")
NUMBERS_EXTENSION = ".numbers"

# Available stamp mount sizes (mm), smallest to largest.
MOUNT_SIZES = [
    20, 22, 24, 25, 27, 28, 29, 30, 33, 34, 35, 36, 39, 40, 41, 42, 44, 46,
    48, 50, 52, 55, 57, 59, 61, 63, 66, 68, 72, 74, 75, 76, 82, 84, 85, 89,
    95, 96, 100, 105, 107, 111, 115, 117, 121, 129, 131, 135, 137, 143, 147,
    151, 158, 167, 171, 175, 181, 188, 192, 198, 201, 215, 216, 231,
]

# Gap (mm) between the mount size and the stamp dimension it's matched
# against, above which we try turning the stamp sideways instead.
MAX_GAP_MM = 3

# Extra length to cut the mount, beyond the stamp's other dimension.
CUT_ALLOWANCE_MM = 5


def smallest_fitting_mount(dimension_mm):
    """Return the smallest mount size >= dimension_mm, or None if too big."""
    for size in MOUNT_SIZES:
        if size >= dimension_mm:
            return size
    return None


def recommend_mount(width_mm, height_mm):
    """Return (mount_size, cut_size, sideways, note) for one stamp."""
    height_mount = smallest_fitting_mount(height_mm)

    if height_mount is not None and (height_mount - height_mm) < MAX_GAP_MM:
        cut_size = width_mm + CUT_ALLOWANCE_MM
        return height_mount, cut_size, False, ""

    # Height match is a poor fit (or doesn't exist) - try the width instead
    # (stamp mounted sideways).
    width_mount = smallest_fitting_mount(width_mm)
    if width_mount is not None:
        cut_size = height_mm + CUT_ALLOWANCE_MM
        return width_mount, cut_size, True, ""

    # Width doesn't fit any mount either. Fall back to the height match if
    # it exists, even though the gap is large.
    if height_mount is not None:
        cut_size = width_mm + CUT_ALLOWANCE_MM
        return height_mount, cut_size, False, "gap >= 3mm, no better width fit"

    return None, None, None, "no mount large enough"


def load_rows(path):
    """Return raw rows (list of list-of-str) from a CSV, Excel, ODS, or Numbers file."""
    ext = os.path.splitext(path)[1].lower()
    if ext in SPREADSHEET_EXTENSIONS:
        rows = load_rows_spreadsheet(path)
    elif ext == NUMBERS_EXTENSION:
        rows = load_rows_numbers(path)
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    return [row for row in rows if row and any(str(cell).strip() for cell in row)]


def load_rows_spreadsheet(path):
    try:
        import pandas as pd
    except ImportError:
        print(
            "Reading .xls/.xlsx/.xlsm/.ods files requires pandas, openpyxl, and odfpy.\n"
            "Install with: pip install pandas openpyxl odfpy",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        df = pd.read_excel(path, header=None, dtype=str)
    except ImportError as e:
        print(
            f"{e}\nInstall with: pip install xlrd openpyxl odfpy",
            file=sys.stderr,
        )
        sys.exit(1)
    df = df.fillna("")
    return df.values.tolist()


def load_rows_numbers(path):
    try:
        from numbers_parser import Document
    except ImportError:
        print(
            "Reading .numbers files requires numbers-parser.\n"
            "Install with: pip install numbers-parser",
            file=sys.stderr,
        )
        sys.exit(1)
    doc = Document(path)
    table = doc.sheets[0].tables[0]
    rows = table.rows(values_only=True)
    return [[_format_numbers_cell(cell) for cell in row] for row in rows]


def _format_numbers_cell(cell):
    """Stringify a Numbers cell, dropping the trailing '.0' Numbers adds to
    whole numbers (numbers_parser returns all numeric cells as float)."""
    if cell is None:
        return ""
    if isinstance(cell, float) and cell.is_integer():
        return str(int(cell))
    return str(cell)


def read_stamps(path):
    """Read (name, catalog_number, width_mm, height_mm) rows from a stamp list file.

    Skips a header row if the width/height columns aren't numeric.
    """
    stamps = []
    rows = load_rows(path)

    if not rows:
        return stamps

    start = 0
    try:
        float(rows[0][2])
        float(rows[0][3])
    except (ValueError, IndexError):
        start = 1  # first row is a header

    for i, row in enumerate(rows[start:], start=start + 1):
        if len(row) < 4:
            print(f"Warning: skipping row {i}, expected 4 columns: {row}", file=sys.stderr)
            continue
        name = row[0].strip()
        catalog_number = row[1].strip()
        try:
            width_mm = float(row[2])
            height_mm = float(row[3])
        except ValueError:
            print(f"Warning: skipping row {i}, non-numeric width/height: {row}", file=sys.stderr)
            continue
        stamps.append((name, catalog_number, width_mm, height_mm))

    return stamps


def fmt(value):
    """Format a number, dropping a trailing '.0'."""
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def build_results(stamps):
    results = []
    for name, catalog_number, width_mm, height_mm in stamps:
        mount_size, cut_size, sideways, note = recommend_mount(width_mm, height_mm)
        results.append({
            "name": name,
            "catalog_number": catalog_number,
            "width_mm": width_mm,
            "height_mm": height_mm,
            "mount_size": mount_size,
            "cut_size": cut_size,
            "sideways": sideways,
            "note": note,
        })
    return results


def write_csv(results, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Stamp Name", "Catalog Number", "Width (mm)", "Height (mm)", "Mount Size (mm) (Scott/Prinz)", "Cut Size (mm)", "Sideways", "Note"])
        for r in results:
            writer.writerow([
                r["name"],
                r["catalog_number"],
                fmt(r["width_mm"]),
                fmt(r["height_mm"]),
                fmt(r["mount_size"]),
                fmt(r["cut_size"]),
                "Yes" if r["sideways"] else ("No" if r["sideways"] is not None else ""),
                r["note"],
            ])


def write_markdown(results, path):
    lines = [
        "# Stamp Mount Guide",
        "",
        "| Stamp Name | Catalog Number | Width (mm) | Height (mm) | Mount Size (mm) (Scott/Prinz) | Cut Size (mm) | Sideways | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        sideways = "Yes" if r["sideways"] else ("No" if r["sideways"] is not None else "")
        mount_size = fmt(r["mount_size"]) if r["mount_size"] is not None else "N/A"
        cut_size = fmt(r["cut_size"]) if r["cut_size"] is not None else "N/A"
        lines.append(f"| {r['name']} | {r['catalog_number']} | {fmt(r['width_mm'])} | {fmt(r['height_mm'])} | {mount_size} | {cut_size} | {sideways} | {r['note']} |")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_bbcode(results, path):
    headers = ["Stamp Name", "Catalog Number", "Width (mm)", "Height (mm)", "Mount Size (mm) (Scott/Prinz)", "Cut Size (mm)", "Sideways", "Note"]
    lines = ["[table]", "[tr]" + "".join(f"[td][b]{h}[/b][/td]" for h in headers) + "[/tr]"]
    for r in results:
        sideways = "Yes" if r["sideways"] else ("No" if r["sideways"] is not None else "")
        mount_size = fmt(r["mount_size"]) if r["mount_size"] is not None else "N/A"
        cut_size = fmt(r["cut_size"]) if r["cut_size"] is not None else "N/A"
        cells = [r["name"], r["catalog_number"], fmt(r["width_mm"]), fmt(r["height_mm"]), mount_size, cut_size, sideways, r["note"]]
        lines.append("[tr]" + "".join(f"[td]{c}[/td]" for c in cells) + "[/tr]")
    lines.append("[/table]")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Recommend stamp mount sizes for a stamp collection.")
    parser.add_argument(
        "input_csv",
        help=(
            "CSV, Excel (.xls/.xlsx/.xlsm), ODS, or Apple Numbers (.numbers) file "
            "with columns: name, catalog_number, width_mm, height_mm"
        ),
    )
    parser.add_argument("-o", "--output-prefix", default="stamp_mounts",
                         help="Prefix for output files (default: stamp_mounts)")
    args = parser.parse_args()

    stamps = read_stamps(args.input_csv)
    if not stamps:
        print("No stamps found in input file.", file=sys.stderr)
        sys.exit(1)

    results = build_results(stamps)

    csv_path = f"{args.output_prefix}.csv"
    md_path = f"{args.output_prefix}.md"
    bbcode_path = f"{args.output_prefix}.bbcode.txt"
    write_csv(results, csv_path)
    write_markdown(results, md_path)
    write_bbcode(results, bbcode_path)

    print(f"Wrote {len(results)} stamps to {csv_path}, {md_path}, and {bbcode_path}")


if __name__ == "__main__":
    main()
