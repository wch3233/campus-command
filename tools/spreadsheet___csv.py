"""
spreadsheet___csv.py — CSV and spreadsheet utilities.

Allows agents to read, write, and summarize CSV data
for data-heavy assignments (statistics, science labs, history data).
"""

import csv
import io
import json
import os
from typing import Any, Optional


def read_csv(filepath: str) -> list[dict]:
    """
    Read a CSV file and return a list of row dicts.

    Args:
        filepath: Path to the .csv file.

    Returns:
        List of dicts, one per row. Keys are column headers.
        Empty list on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:
        print(f"[csv] File not found: {filepath}")
        return []
    except Exception as e:
        print(f"[csv] Read error: {e}")
        return []


def write_csv(filepath: str, rows: list[dict], fieldnames: list[str] = None) -> bool:
    """
    Write a list of dicts to a CSV file.

    Args:
        filepath:   Destination path.
        rows:       List of row dicts.
        fieldnames: Column order. Inferred from first row if omitted.

    Returns:
        True on success, False on failure.
    """
    if not rows:
        return False
    try:
        fieldnames = fieldnames or list(rows[0].keys())
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        print(f"[csv] Write error: {e}")
        return False


def summarize_csv(rows: list[dict], max_rows: int = 10) -> str:
    """
    Produce a readable summary of CSV data suitable for prompt injection.

    Args:
        rows:     Data from read_csv().
        max_rows: Max number of rows to include in the summary.

    Returns:
        String summary.
    """
    if not rows:
        return "No data."

    headers = list(rows[0].keys())
    sample = rows[:max_rows]

    lines = [f"Columns: {', '.join(headers)}", f"Total rows: {len(rows)}", ""]

    # Build table
    col_widths = {h: max(len(h), max(len(str(r.get(h, ""))) for r in sample)) for h in headers}
    header_row = " | ".join(h.ljust(col_widths[h]) for h in headers)
    lines.append(header_row)
    lines.append("-" * len(header_row))

    for row in sample:
        lines.append(" | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers))

    if len(rows) > max_rows:
        lines.append(f"... ({len(rows) - max_rows} more rows)")

    return "\n".join(lines)


def compute_stats(rows: list[dict], column: str) -> Optional[dict]:
    """
    Compute basic descriptive statistics for a numeric column.

    Args:
        rows:   Data rows.
        column: Column name to analyze.

    Returns:
        Dict with count, min, max, mean, sum; or None on error.
    """
    try:
        values = [float(row[column]) for row in rows if row.get(column) not in (None, "")]
        if not values:
            return None
        return {
            "column": column,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "sum": sum(values),
        }
    except (ValueError, KeyError) as e:
        print(f"[csv] Stats error for column '{column}': {e}")
        return None
