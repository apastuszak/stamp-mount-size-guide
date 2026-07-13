# stamp-mount-size-guide

A command-line tool that reads a list of stamps and figures out which
[Scott/Prinz](https://en.wikipedia.org/wiki/Stamp_mount) stamp mount size to
use for each one, plus how wide to cut the mount strip.

## What it does

Stamp mounts are sold as strips of fixed height; you cut the strip to the
width you need and slide the stamp in from the side. This tool automates
picking the right strip height and cut length for every stamp in a
collection:

1. For each stamp, find the smallest available mount size that is **at least
   as tall as the stamp's height**.
2. If that mount is within 3mm of the stamp's height, use it: cut the strip
   to the stamp's **width + 5mm**.
3. If the gap is 3mm or more (a loose fit), try mounting the stamp
   **sideways** instead — match the mount size against the stamp's width, and
   cut the strip to the stamp's **height + 5mm**.
4. If neither orientation gets within 3mm, use whichever mount is the
   closer fit and flag it in the Note column with how much bigger it is
   and a suggestion to use a Hawid glue pen to make a custom mount instead.
5. If a stamp is too large for the largest available mount in both
   orientations, it's flagged the same way, with no mount size given.

The 5mm cut allowance leaves clearance to slide the stamp in and out of the
mount without splitting the seams.

## Requirements

- Python 3.9+
- No dependencies for CSV input.
- Optional dependencies for other input formats (see below).

Install optional dependencies with:

```sh
pip install -r requirements.txt
```

or individually:

```sh
pip install pandas openpyxl odfpy   # Excel (.xlsx/.xlsm) and ODS input
pip install xlrd                    # legacy Excel (.xls) input
pip install numbers-parser          # Apple Numbers (.numbers) input
```

## Usage

```sh
python3 stamp_mount_guide.py <input_file> [-o output_prefix]
```

- `input_file` — a CSV, Excel (`.xls`/`.xlsx`/`.xlsm`), OpenDocument
  Spreadsheet (`.ods`), or Apple Numbers (`.numbers`) file. The format is
  detected from the file extension.
- `-o`, `--output-prefix` — base name for the generated output files
  (default: `stamp_mounts`).

Example:

```sh
python3 stamp_mount_guide.py stamps.csv -o stamp_mounts
```

This writes `stamp_mounts.csv`, `stamp_mounts.md`, `stamp_mounts.bbcode.txt`,
`stamp_mounts_checklist.csv`, `stamp_mounts_checklist.md`, and
`stamp_mounts_checklist.bbcode.txt` to the current directory.

## Input format

The input file needs four columns, in this order:

| Column         | Description                                   |
| -------------- | --------------------------------------------- |
| Stamp Name     | Any text                                      |
| Catalog Number | Any text (e.g. Scott number, block reference) |
| Width (mm)     | Stamp width in millimeters                    |
| Height (mm)    | Stamp height in millimeters                   |

A header row is optional — the script auto-detects one by checking whether
the width/height columns of the first row are numeric. If they aren't, that
row is treated as a header and skipped.

Rows with missing or non-numeric width/height are skipped with a warning
printed to stderr; everything else is still processed.

Example CSV:

```csv
Mother' Day,2238,40,28
"Infantry Day: ""Salt of the Earth""",2240,51,37
Lighthouses of Ukraine,Block 210 (2205-2210),123,170
```

## Output formats

Every run produces the same data in three formats:

- **`<prefix>.csv`** — spreadsheet-friendly CSV.
- **`<prefix>.md`** — a Markdown table.
- **`<prefix>.bbcode.txt`** — a `[table]`/`[tr]`/`[td]` BBCode table, for
  pasting into forum posts.

Each output has these columns:

| Column                        | Meaning                                                                 |
| ----------------------------- | ----------------------------------------------------------------------- |
| Stamp Name                    | From the input                                                          |
| Catalog Number                | From the input                                                          |
| Width (mm)                    | From the input                                                          |
| Height (mm)                   | From the input                                                          |
| Mount Size (mm) (Scott/Prinz) | Recommended mount strip size                                            |
| Cut Size (mm)                 | How wide to cut the strip                                               |
| Sideways                      | `Yes` if the stamp should be mounted sideways, `No` otherwise           |
| Box Height (mm)               | Mount size + 2mm (cut size + 2mm if sideways), for sizing a storage box |
| Note                          | Explains any fallback (e.g. no mount is large enough)                   |

## Mount checklist

Alongside the per-stamp results, the tool also writes a shopping/cutting
checklist that aggregates how many mount strips of each size are needed
across the whole collection:

- **`<prefix>_checklist.csv`** — one row per mount size.
- **`<prefix>_checklist.md`** — the same data as a Markdown task list
  (`- [ ]`), so you can check off sizes as you cut or buy them.
- **`<prefix>_checklist.bbcode.txt`** — a `[table]`/`[tr]`/`[td]` BBCode
  table, for pasting into forum posts.

The checklist has these columns (CSV/BBCode) or per-item details (Markdown):

| Column                        | Meaning                            |
| ----------------------------- | ---------------------------------- |
| Mount Size (mm) (Scott/Prinz) | The stock mount size               |
| Number of Stamps              | Number of stamps needing that size |

Stamps with no fitting stock mount (flagged for a custom Hawid glue pen
mount) are excluded from the checklist.

## Available mount sizes

The tool chooses from these standard mount heights (mm):

```text
20, 22, 24, 25, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36, 37,
39, 40, 41, 42, 44, 45, 46, 48, 50, 52, 55, 57, 59, 61, 63,
66, 68, 70, 72, 74, 75, 76, 80, 82, 84, 85, 89, 91, 95, 96,
100, 105, 107, 109, 111, 115, 117, 120, 121, 127, 129, 131, 135, 137, 139,
143, 147, 151, 158, 163, 167, 171, 175, 181, 185, 188, 192, 198, 201, 207,
215, 216, 231
```

To use a different set of sizes, edit the `MOUNT_SIZES` list at the top of
[stamp_mount_guide.py](stamp_mount_guide.py).

## Tuning the fit

Two constants in [stamp_mount_guide.py](stamp_mount_guide.py) control the
matching behavior:

- `MAX_GAP_MM` (default `3`) — the maximum acceptable gap between a mount
  size and the stamp dimension before the script tries a sideways fit
  instead.
- `CUT_ALLOWANCE_MM` (default `5`) — how much extra length to add when
  cutting the mount strip.
