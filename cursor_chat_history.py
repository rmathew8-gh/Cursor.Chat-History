#!/usr/bin/env python3
import duckdb
import json
from pathlib import Path
import os
import sys
import logging
from typing import List, Optional, Dict, Any, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    text: str
    # Add more fields if needed


class CursorChatHistoryExporter:
    def __init__(
        self, base_dir: Optional[str] = None, output_dir: str = "chat_history_exports"
    ):
        if base_dir is not None:
            self.base_dir = base_dir
        else:
            if sys.platform == "darwin":
                # macOS default path
                self.base_dir = str(
                    Path(os.path.expanduser("~")) / "Library/Application Support/Cursor/User/workspaceStorage"
                )
            else:
                # Linux/Windows default path
                self.base_dir = str(
                    Path(os.path.expanduser("~")) / ".config/Cursor/User/workspaceStorage"
                )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    @staticmethod
    def find_vscdb_files(base_dir: str) -> List[Path]:
        """Recursively find all state.vscdb files in subdirectories of base_dir."""
        return list(Path(base_dir).rglob("state.vscdb"))

    @staticmethod
    def get_table_names(db_path: Path) -> List[str]:
        try:
            with duckdb.connect(database=":memory:") as con:
                con.execute(f"ATTACH DATABASE '{db_path}' AS db;")
                tables = con.execute(
                    "SELECT name FROM main.sqlite_master WHERE type='table';"
                ).fetchall()
                return [t[0] for t in tables]
        except Exception as e:
            logging.error(f"Error reading tables from {db_path}: {e}")
            return []

    @staticmethod
    def export_prompts_to_org(prompts: Iterable[Prompt], output_file: Path) -> None:
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(f"* {prompt.text.replace('\n', '\n')}\n" for prompt in prompts)

    @staticmethod
    def parse_prompts(raw_prompts: Any) -> Optional[List[Prompt]]:
        if isinstance(raw_prompts, list):
            # Use map and filter to process prompts
            return list(
                map(
                    lambda entry: Prompt(text=entry.get("text", "")),
                    filter(
                        lambda entry: isinstance(entry, dict) and "text" in entry,
                        raw_prompts,
                    ),
                )
            )
        return None

    @staticmethod
    def extract_ai_service_prompts(db_path: Path) -> Optional[List[Dict[str, Any]]]:
        try:
            with duckdb.connect(database=":memory:") as con:
                con.execute(f"ATTACH DATABASE '{db_path}' AS db;")
                tables = con.execute(
                    "SELECT name FROM main.sqlite_master WHERE type='table';"
                ).fetchall()
                if not any(t[0] == "ItemTable" for t in tables):
                    return None
                row = con.execute(
                    "SELECT value FROM db.ItemTable WHERE key='aiService.prompts';"
                ).fetchone()
                if not row:
                    return None
                value = row[0]
                try:
                    raw_prompts = json.loads(value)
                    prompts = CursorChatHistoryExporter.parse_prompts(raw_prompts)
                    # Return as list of dicts for backward compatibility
                    return [prompt.__dict__ for prompt in prompts] if prompts else None
                except Exception:
                    return None
        except Exception as e:
            logging.error(f"Error extracting aiService.prompts from {db_path}: {e}")
            return None
        return None

    def export_all(self, single_file: Optional[Path] = None) -> None:
        def process_db(db_path: Path) -> Optional[str]:
            prompts = self.extract_ai_service_prompts(db_path)
            if prompts:
                workspace_id = db_path.parent.name
                output_file = self.output_dir / f"aiService_prompts_{workspace_id}.org"
                # Use map to convert dicts to Prompt dataclass
                prompt_objs = map(lambda d: Prompt(**d), prompts)
                self.export_prompts_to_org(prompt_objs, output_file)
                logging.info(f"Exported aiService.prompts to {output_file}")
                return str(output_file)
            else:
                logging.info(f"No aiService.prompts found in {db_path}")
                return None

        if single_file:
            if not single_file.exists():
                logging.error(f"File {single_file} does not exist.")
                sys.exit(1)
            vscdb_files = [single_file]
            logging.info(f"Running in single-file mode on {single_file}")
        else:
            vscdb_files = self.find_vscdb_files(self.base_dir)
            logging.info(
                f"Running in multi-workspace mode, found {len(vscdb_files)} files."
            )
        if not vscdb_files:
            logging.warning("No .vscdb files found.")
            return
        # Use functional style to process all db files
        list(map(process_db, vscdb_files))


def extract_ai_service_prompts(db_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Module-level function for backward compatibility with tests."""
    return CursorChatHistoryExporter.extract_ai_service_prompts(db_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    exporter = CursorChatHistoryExporter()
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
        exporter.export_all(single_file=db_path)
    else:
        exporter.export_all()


if __name__ == "__main__":
    main()
