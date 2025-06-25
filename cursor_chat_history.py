#!/usr/bin/env python3
import duckdb
import json
from pathlib import Path
import os
import sys
import logging
from typing import List, Optional, Dict, Any

def find_vscdb_files(base_dir: str) -> List[Path]:
    """Recursively find all state.vscdb files in subdirectories of base_dir."""
    return list(Path(base_dir).rglob('state.vscdb'))


def get_table_names(db_path: Path) -> List[str]:
    """Return a list of table names in the SQLite DB using DuckDB."""
    try:
        con = duckdb.connect(database=':memory:')
        con.execute(f"ATTACH DATABASE '{db_path}' AS db;")
        tables = con.execute("SELECT name FROM main.sqlite_master WHERE type='table';").fetchall()
        con.close()
        return [t[0] for t in tables]
    except Exception as e:
        logging.error(f"Error reading tables from {db_path}: {e}")
        return []

def export_prompts_to_org(prompts: List[Dict[str, Any]], output_file: Path) -> None:
    """Export a list of prompt dicts to an org-mode file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in prompts:
            text = entry.get('text', '').replace('\n', '\n')
            f.write(f"* {text}\n")

def extract_ai_service_prompts(db_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Extract aiService.prompts from the ItemTable in the given vscdb file."""
    try:
        con = duckdb.connect(database=':memory:')
        con.execute(f"ATTACH DATABASE '{db_path}' AS db;")
        tables = con.execute("SELECT name FROM main.sqlite_master WHERE type='table';").fetchall()
        if not any(t[0] == 'ItemTable' for t in tables):
            return None
        row = con.execute("SELECT value FROM db.ItemTable WHERE key='aiService.prompts';").fetchone()
        if not row:
            return None
        value = row[0]
        try:
            prompts = json.loads(value)
            if isinstance(prompts, list):
                return prompts
        except Exception:
            return None
    except Exception as e:
        logging.error(f"Error extracting aiService.prompts from {db_path}: {e}")
        return None
    return None

def main() -> None:
    """Main entry point: finds vscdb files, extracts prompts, and exports them."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    linux_cursor_dir = Path(os.path.expanduser("~")) / ".config/Cursor/User/workspaceStorage"
    output_dir = Path("chat_history_exports")
    output_dir.mkdir(exist_ok=True)

    # Check for command-line argument
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
        if not db_path.exists():
            logging.error(f"File {db_path} does not exist.")
            sys.exit(1)
        vscdb_files = [db_path]
        logging.info(f"Running in single-file mode on {db_path}")
    else:
        vscdb_files = find_vscdb_files(str(linux_cursor_dir))
        logging.info(f"Running in multi-workspace mode, found {len(vscdb_files)} files.")
    if not vscdb_files:
        logging.warning("No .vscdb files found.")
        return
    for db_path in vscdb_files:
        prompts = extract_ai_service_prompts(db_path)
        if prompts:
            workspace_id = db_path.parent.name
            output_file = output_dir / f"aiService_prompts_{workspace_id}.org"
            export_prompts_to_org(prompts, output_file)
            logging.info(f"Exported aiService.prompts to {output_file}")
        else:
            logging.info(f"No aiService.prompts found in {db_path}")

if __name__ == "__main__":
    main() 