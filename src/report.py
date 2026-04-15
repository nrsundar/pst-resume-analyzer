"""Merge batch results and write the final resume extraction report."""

import json
from datetime import datetime
from pathlib import Path


def merge_results(all_results: list[dict]) -> dict:
    """Deduplicate and merge all batch results into a single summary."""
    merged = {
        "projects": [],
        "skills": set(),
        "achievements": [],
        "responsibilities": [],
        "collaborations": [],
        "notes": [],
    }
    seen_projects: set[str] = set()
    seen_achievements: set[str] = set()
    seen_responsibilities: set[str] = set()

    for result in all_results:
        if "raw_response" in result:
            merged["notes"].append(result["raw_response"])
            continue

        for proj in result.get("projects", []):
            key = f"{proj.get('name', '')}|{proj.get('description', '')[:60]}"
            if key not in seen_projects:
                seen_projects.add(key)
                merged["projects"].append(proj)

        for skill in result.get("skills", []):
            merged["skills"].add(skill.lower().strip())

        for ach in result.get("achievements", []):
            norm = ach.strip().lower()
            if norm not in seen_achievements:
                seen_achievements.add(norm)
                merged["achievements"].append(ach)

        for resp in result.get("responsibilities", []):
            norm = resp.strip().lower()
            if norm not in seen_responsibilities:
                seen_responsibilities.add(norm)
                merged["responsibilities"].append(resp)

        merged["collaborations"].extend(result.get("collaborations", []))

        note = result.get("notes", "")
        if note:
            merged["notes"].append(note)

    merged["skills"] = sorted(merged["skills"])
    merged["collaborations"] = sorted(set(merged["collaborations"]))
    return merged


def _section(lines: list[str], title: str):
    lines.append(f"\n## {title}\n")


def write_report(all_results: list[dict], output_dir: Path) -> tuple[Path, Path]:
    """Write txt and json reports to output_dir. Returns (txt_path, json_path)."""
    merged = merge_results(all_results)

    lines = [
        "=" * 70,
        "RESUME EXTRACTION REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 70,
    ]

    _section(lines, "PROJECTS")
    for p in merged["projects"]:
        lines.append(f"  Project : {p.get('name', 'Unnamed')}")
        if p.get("description"):
            lines.append(f"  Desc    : {p['description']}")
        if p.get("outcome"):
            lines.append(f"  Outcome : {p['outcome']}")
        if p.get("approx_date"):
            lines.append(f"  Date    : {p['approx_date']}")
        lines.append("")

    _section(lines, "SKILLS & TECHNOLOGIES")
    for skill in merged["skills"]:
        lines.append(f"  - {skill}")

    _section(lines, "ACHIEVEMENTS")
    for ach in merged["achievements"]:
        lines.append(f"  • {ach}")

    _section(lines, "RESPONSIBILITIES")
    for resp in merged["responsibilities"]:
        lines.append(f"  • {resp}")

    _section(lines, "COLLABORATIONS")
    for col in merged["collaborations"]:
        lines.append(f"  • {col}")

    _section(lines, "ADDITIONAL NOTES")
    for note in merged["notes"]:
        if note:
            lines.append(f"  {note}")

    report_path = output_dir / "resume_extraction.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    json_path = output_dir / "resume_extraction.json"
    json_path.write_text(json.dumps(merged, indent=2, default=list), encoding="utf-8")

    return report_path, json_path
