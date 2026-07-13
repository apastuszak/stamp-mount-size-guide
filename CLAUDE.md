# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file Python CLI (`stamp_mount_guide.py`, no package structure) that reads a list of stamps
(name, catalog number, width, height in mm) and, for each stamp, recommends a [Scott/Prinz](https://en.wikipedia.org/wiki/Stamp_mount)
stamp mount strip size, how wide to cut it, and a storage box size. It also produces a shopping/cutting
checklist aggregating how many mount strips of each size are needed across the whole collection.

## Commands

Run the tool:

```sh
python3 stamp_mount_guide.py <input_file> [-o output_prefix]
```

`<input_file>` can be `.csv`, `.xls`/`.xlsx`/`.xlsm`, `.ods`, or `.numbers`, with columns
`name, catalog_number, width_mm, height_mm` (header row optional — auto-detected).

Install optional dependencies (only needed for non-CSV input formats):

```sh
pip install -r requirements.txt
```

There is no test suite, build step, or linter configured in this repo. The `stamps.*` sample files and
generated `stamp_mounts*` output files in the repo root are the maintainer's personal collection data —
they're gitignored (see `.gitignore`) and should not be committed. Verify changes by running the script
against `stamps.csv` and inspecting the output, e.g.:

```sh
python3 stamp_mount_guide.py stamps.csv -o /tmp/test_out
```

## Architecture

Everything lives in `stamp_mount_guide.py`, organized as a pipeline:

1. **`read_stamps` / `load_rows*`** — format-dispatching input loader. `load_rows` picks a loader based on
   file extension (`load_rows_spreadsheet` via pandas for Excel/ODS, `load_rows_numbers` via
   `numbers_parser` for Apple Numbers, plain `csv.reader` otherwise), returning raw string rows. Optional
   dependencies are imported lazily inside these functions so plain CSV usage never requires them.
2. **`recommend_mount`** — the core sizing logic. Tries the stamp's height against `MOUNT_SIZES` first; if
   the smallest fitting mount is within `MAX_GAP_MM` of the stamp, uses it. Otherwise tries the width
   (mounting the stamp sideways). If neither orientation is a close fit, falls back to whichever is
   closest and flags it in a note as needing a custom (Hawid glue pen) mount. Returns
   `(mount_size, cut_size, sideways, note)`.
3. **`build_results`** — calls `recommend_mount` per stamp and derives the box dimensions from it. Box
   height/width are *swapped* depending on orientation: non-sideways stamps get
   `box_height = mount_size + BOX_ALLOWANCE_MM` and `box_width = cut_size`; sideways stamps get the
   opposite. This inversion is the trickiest part of the logic to get right when editing — box height
   always corresponds to the mount strip's height regardless of stamp orientation.
4. **`write_csv` / `write_markdown` / `write_bbcode`** — three parallel renderers of the same per-stamp
   result rows (CSV, Markdown table, and `[table]`/`[tr]`/`[td]` BBCode for forum posts). Column order and
   set must be kept in sync across all three when adding/removing a column.
5. **`build_checklist` / `write_checklist_csv` / `write_checklist_markdown` / `write_checklist_bbcode`** —
   a second, separate pipeline that aggregates `build_results` output by mount size (excluding stamps with
   no fitting mount) into a shopping/cutting checklist, again rendered in the same three formats.
6. **`main`** — wires the above together and writes 6 output files: `<prefix>.{csv,md,bbcode.txt}` and
   `<prefix>_checklist.{csv,md,bbcode.txt}`.

Tunable constants at the top of the file: `MOUNT_SIZES` (the stock mount heights available, must stay
sorted ascending since `smallest_fitting_mount` relies on that), `MAX_GAP_MM`, `CUT_ALLOWANCE_MM`, and
`BOX_ALLOWANCE_MM`.

When adding a new per-stamp output column, it needs to be threaded through `build_results`'s result dict
and all three of `write_csv`/`write_markdown`/`write_bbcode` (and their README documentation table) to stay
consistent.
