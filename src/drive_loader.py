# src/drive_loader.py
"""
Simple Drive loader for 'Anyone with the link' Excel files.
"""

import re
from typing import List
import pandas as pd

# Detect Google Drive FILE_ID inside a URL
DRIVE_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]{10,})|id=([a-zA-Z0-9_-]{10,})")

def extract_drive_id(url_or_id: str) -> str:
    """Extract Google Drive file ID from URL or direct ID."""
    if not url_or_id:
        raise ValueError("Empty Drive URL/ID.")

    # Case 1: Direct ID (simple)
    if re.fullmatch(r"[a-zA-Z0-9_-]{10,}", url_or_id):
        return url_or_id

    # Case 2: ID inside URL
    m = DRIVE_ID_RE.search(url_or_id)
    if m:
        return m.group(1) or m.group(2)

    # Case 3: Extract any long token
    tokens = re.findall(r"[a-zA-Z0-9_-]{10,}", url_or_id)
    if tokens:
        return tokens[0]

    raise ValueError(f"Could not extract Drive file id from: {url_or_id}")


def build_uc_url(file_id: str) -> str:
    """Direct download link for pandas."""
    return f"https://drive.google.com/uc?id={file_id}"


def load_single_from_drive(url_or_id: str, sheet_name=0, **pd_read_kwargs) -> pd.DataFrame:
    """Load a single Google Drive Excel file."""
    fid = extract_drive_id(url_or_id)
    url = build_uc_url(fid)

    try:
        df = pd.read_excel(
            url,
            sheet_name=sheet_name,
            engine="openpyxl",
            **pd_read_kwargs
        )
        return df

    except Exception as e:
        raise RuntimeError(f"Failed to read Drive file {url_or_id} -> {e}")


def load_multiple_from_drive(file_ids_or_urls: List[str], sheet_name=0, concat: bool = True, **pd_read_kwargs):
    """Load multiple Drive Excel files (concat=True = merge into one DF)."""
    dfs = []
    errors = []

    for u in file_ids_or_urls:
        try:
            df = load_single_from_drive(u, sheet_name=sheet_name, **pd_read_kwargs)
            dfs.append(df)
        except Exception as exc:
            errors.append((u, str(exc)))
            print(f"[drive_loader] warning: failed to load {u}: {exc}")

    if not dfs:
        raise RuntimeError(f"No files loaded successfully. Errors: {errors}")

    if concat:
        try:
            combined = pd.concat(dfs, ignore_index=True)
            return combined
        except Exception as e:
            print(f"[drive_loader] concat failed: {e}. Returning list.")
            return dfs

    return dfs
