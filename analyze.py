#!/usr/bin/env python3
"""
PST Resume Analyzer
-------------------
Analyzes an Outlook .pst archive and extracts resume-relevant information
(projects, skills, achievements, responsibilities).

Usage:
    python analyze.py                            # full run using config.yaml
    python analyze.py --role "Sr.SA Manager"     # tailor extraction for a role
    python analyze.py --test 200                 # test with first 200 emails
    python analyze.py --resume                   # resume from last checkpoint
    python analyze.py --pst path/to/file.pst     # override pst path
    python analyze.py --model haiku              # use a different model
    python analyze.py --folders                  # list folders in the PST and exit
"""

import os
import sys
import argparse
from pathlib import Path

import yaml

# Load API key from .env if not already in environment
_env_file = Path(__file__).parent / ".env"
if _env_file.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = _line.split("=", 1)[1].strip().strip("'\"")
            break

import pypff
from src.pst_reader import iter_messages, list_folders
from src.analyzer import analyze_batch, format_email
from src.report import write_report
from src.checkpoint import Checkpoint


def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a .pst email archive and extract resume-relevant information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pst",     help="Path to .pst file (overrides config.yaml)")
    parser.add_argument("--output",  help="Output directory (overrides config.yaml)")
    parser.add_argument("--model",   help="Model ID (overrides config.yaml)")
    parser.add_argument("--config",  default="config.yaml", help="Path to config file")
    parser.add_argument("--role",    default="", metavar="ROLE",
                        help='Target role to tailor extraction for, e.g. "Sr.SA Manager"')
    parser.add_argument("--test",    type=int, default=0, metavar="N",
                        help="Only process first N emails (for testing/cost estimation)")
    parser.add_argument("--resume",  action="store_true",
                        help="Resume from last saved checkpoint")
    parser.add_argument("--folders", action="store_true",
                        help="List all folders in the PST with message counts and exit")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    pst_path     = Path(args.pst    or config["pst_path"])
    output_dir   = Path(args.output or config.get("output_dir", "output"))
    model        = args.model       or config.get("model", "claude-sonnet-4-6")
    batch_size   = config.get("batch_size", 50)
    max_body     = config.get("max_body_chars", 500)
    skip_folders = set(config.get("skip_folders", []))
    test_limit   = args.test
    role         = args.role or config.get("role", "")

    if not pst_path.exists():
        print(f"Error: PST file not found: {pst_path}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    pst = pypff.file()
    pst.open(str(pst_path))
    root = pst.get_root_folder()

    # --folders: just print folder tree and exit
    if args.folders:
        folders = list_folders(root, skip_folders)
        print(f"{'FOLDER':<60} {'MSGS':>6}  STATUS")
        print("-" * 72)
        for f in folders:
            indent = "  " * f["depth"]
            status = "SKIP" if f["skipped"] else ""
            print(f"  {indent}{f['path']:<58} {f['messages']:>6}  {status}")
        pst.close()
        return

    print("PST Resume Analyzer")
    print(f"  PST    : {pst_path}")
    print(f"  Model  : {model}")
    print(f"  Output : {output_dir}")
    if role:
        print(f"  Role   : {role}")
    if test_limit:
        print(f"  Mode   : TEST ({test_limit} emails only)")
    print()

    checkpoint = Checkpoint(output_dir / "checkpoint.json")
    all_results: list[dict] = []
    emails_already_done = 0

    if args.resume and checkpoint.exists():
        all_results, emails_already_done = checkpoint.load()
        print(f"Resuming from checkpoint: {emails_already_done:,} emails already processed\n")

    batch: list[str] = []
    total_emails = emails_already_done
    total_batches = 0
    skipped = 0

    for folder_path, message in iter_messages(root, skip_folders):
        # Skip emails already processed in a previous run
        if skipped < emails_already_done:
            skipped += 1
            continue

        if test_limit and (total_emails - emails_already_done) >= test_limit:
            break

        try:
            formatted = format_email(folder_path, message, max_body)
        except Exception:
            continue

        batch.append(formatted)
        total_emails += 1

        if len(batch) >= batch_size:
            total_batches += 1
            print(f"  Batch {total_batches:4d} | {total_emails:6,} emails processed ...", end=" ", flush=True)
            try:
                result = analyze_batch(batch, model, role)
                all_results.append(result)
                n_proj  = len(result.get("projects", []))
                n_skill = len(result.get("skills", []))
                print(f"projects: {n_proj}, skills: {n_skill}")
            except Exception as e:
                print(f"ERROR: {e}")
            batch = []

            # Checkpoint every 10 batches so long runs can be resumed
            if total_batches % 10 == 0:
                checkpoint.save(all_results, total_emails)
                print(f"  [Checkpoint saved: {total_emails:,} emails]")

    # Final partial batch
    if batch:
        total_batches += 1
        print(f"  Batch {total_batches:4d} | {total_emails:6,} emails (final) ...", end=" ", flush=True)
        try:
            result = analyze_batch(batch, model, role)
            all_results.append(result)
            print("done")
        except Exception as e:
            print(f"ERROR: {e}")

    pst.close()

    print(f"\nProcessed {total_emails:,} emails in {total_batches} batches.")
    print("Merging results and writing report ...")

    report_path, json_path = write_report(all_results, output_dir)
    checkpoint.delete()

    print(f"\nDone!")
    print(f"  Report : {report_path}")
    print(f"  JSON   : {json_path}")


if __name__ == "__main__":
    main()
