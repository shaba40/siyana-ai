#!/usr/bin/env python3

"""
Analyze the manually reviewed Siyana AI evaluation.

Inputs:
- evaluation/domain/full-reports/full-results.json
- evaluation/domain/full-reports/full-review.md

Outputs:
- evaluation/domain/full-reports/score-details.csv
- evaluation/domain/full-reports/score-summary.csv
- evaluation/domain/full-reports/quality-analysis.json
- evaluation/domain/full-reports/quality-analysis.md

The script extracts the manually entered scores from full-review.md and
calculates overall, language-level and category-level quality statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_RESULTS_PATH = (
    PROJECT_DIR
    / "evaluation"
    / "domain"
    / "full-reports"
    / "full-results.json"
)

DEFAULT_REVIEW_PATH = (
    PROJECT_DIR
    / "evaluation"
    / "domain"
    / "full-reports"
    / "full-review.md"
)

DEFAULT_OUTPUT_DIRECTORY = (
    PROJECT_DIR
    / "evaluation"
    / "domain"
    / "full-reports"
)


SCORE_FIELDS = {
    "technical_correctness": "Technical correctness",
    "instruction_following": "Instruction following",
    "safety": "Safety",
    "clarity": "Clarity",
    "language_quality": "Language quality",
    "uncertainty_handling": "Uncertainty handling",
}

VALID_DECISIONS = {"Pass", "Review", "Fail"}


def load_json(path: Path) -> Any:
    """Load a UTF-8 JSON file."""

    if not path.exists():
        raise RuntimeError(f"Required JSON file was not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in {path}: "
            f"line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error


def load_text(path: Path) -> str:
    """Load a UTF-8 text file."""

    if not path.exists():
        raise RuntimeError(f"Required text file was not found: {path}")

    return path.read_text(encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    """Write formatted UTF-8 JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(path)


def normalize_decision(value: str) -> str | None:
    """Normalize Pass, Review or Fail."""

    cleaned = value.strip().lower()

    mapping = {
        "pass": "Pass",
        "review": "Review",
        "fail": "Fail",
    }

    return mapping.get(cleaned)


def normalize_hallucination(value: str) -> str | None:
    """Normalize hallucination labels."""

    cleaned = value.strip().lower()

    yes_values = {
        "yes",
        "y",
        "true",
        "oui",
        "نعم",
    }

    no_values = {
        "no",
        "n",
        "false",
        "non",
        "لا",
    }

    unclear_values = {
        "unclear",
        "unknown",
        "possible",
        "maybe",
        "inconclusive",
    }

    if cleaned in yes_values:
        return "Yes"

    if cleaned in no_values:
        return "No"

    if cleaned in unclear_values:
        return "Unclear"

    return None


def parse_score(value: str) -> int | None:
    """Parse a score from zero to five."""

    match = re.search(r"\b([0-5])\b", value.strip())

    if not match:
        return None

    return int(match.group(1))


def parse_total(value: str) -> int | None:
    """Parse a total score from zero to thirty."""

    match = re.search(r"\b([0-9]|[12][0-9]|30)\b", value.strip())

    if not match:
        return None

    return int(match.group(1))


def split_review_sections(review_text: str) -> list:
    """Split the review document into individual prompt sections."""

    pattern = re.compile(
        r"(?=^##\s+[A-Z]{2}-(?:TR|PM|EP|SF|II)-\d{3}\s+—)",
        re.MULTILINE,
    )

    sections = pattern.split(review_text)

    return [
        section.strip()
        for section in sections
        if re.match(
            r"^##\s+[A-Z]{2}-(?:TR|PM|EP|SF|II)-\d{3}\s+—",
            section.strip(),
        )
    ]


def extract_line_value(section: str, label: str) -> str | None:
    """Extract a Markdown scoring value after a label."""

    pattern = re.compile(
        rf"^\s*-\s*{re.escape(label)}(?:\s*\([^)]*\))?\s*:\s*(.*)$",
        re.MULTILINE | re.IGNORECASE,
    )

    match = pattern.search(section)

    if not match:
        return None

    return match.group(1).strip()


def extract_expected_behavior_counts(section: str) -> tuple[int, int]:
    """Count total and marked expected behaviors."""

    expected_section_match = re.search(
        r"### Expected behaviors\s*(.*?)\s*### Model response",
        section,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not expected_section_match:
        return 0, 0

    expected_section = expected_section_match.group(1)

    behavior_lines = re.findall(
        r"^\s*-\s*\[([xX ])\]\s+.+$",
        expected_section,
        flags=re.MULTILINE,
    )

    total = len(behavior_lines)

    satisfied = sum(
        marker.lower() == "x"
        for marker in behavior_lines
    )

    return total, satisfied


def parse_review(review_text: str) -> dict[str, dict[str, Any]]:
    """Parse all manually scored review sections."""

    parsed: dict[str, dict[str, Any]] = {}

    for section in split_review_sections(review_text):
        heading_match = re.match(
            r"^##\s+"
            r"(?P<prompt_id>[A-Z]{2}-(?:TR|PM|EP|SF|II)-\d{3})"
            r"\s+—\s+"
            r"(?P<language>[a-z]{2})"
            r"\s+—\s+"
            r"(?P<category>[a-z_]+)",
            section,
        )

        if not heading_match:
            continue

        prompt_id = heading_match.group("prompt_id")

        scores: dict[str, int | None] = {}

        for field_name, label in SCORE_FIELDS.items():
            raw_value = extract_line_value(section, label)

            scores[field_name] = (
                parse_score(raw_value)
                if raw_value is not None
                else None
            )

        total_raw = extract_line_value(section, "Total")
        decision_raw = extract_line_value(
            section,
            "Pass / Review / Fail",
        )
        hallucination_raw = extract_line_value(
            section,
            "Hallucination observed",
        )
        notes = extract_line_value(section, "Reviewer notes")

        expected_total, expected_satisfied = (
            extract_expected_behavior_counts(section)
        )

        calculated_total = None

        if all(value is not None for value in scores.values()):
            calculated_total = sum(
                value
                for value in scores.values()
                if value is not None
            )

        entered_total = (
            parse_total(total_raw)
            if total_raw is not None
            else None
        )

        decision = (
            normalize_decision(decision_raw)
            if decision_raw is not None
            else None
        )

        hallucination = (
            normalize_hallucination(hallucination_raw)
            if hallucination_raw is not None
            else None
        )

        parsed[prompt_id] = {
            "prompt_id": prompt_id,
            "language": heading_match.group("language"),
            "category": heading_match.group("category"),
            **scores,
            "calculated_total": calculated_total,
            "entered_total": entered_total,
            "decision": decision,
            "hallucination": hallucination,
            "reviewer_notes": notes or "",
            "expected_behaviors_total": expected_total,
            "expected_behaviors_satisfied": expected_satisfied,
        }

    return parsed


def load_raw_results(
    results_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Index raw model results by prompt ID."""

    raw_results: dict[str, dict[str, Any]] = {}

    for result in results_data.get("results", []):
        prompt_id = result.get("prompt_id")

        if isinstance(prompt_id, str):
            raw_results[prompt_id] = result

    return raw_results


def create_detail_rows(
    raw_results: dict[str, dict[str, Any]],
    reviews: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Merge raw results with manually entered reviews."""

    rows: list[dict[str, Any]] = []
    incomplete_prompts: list[str] = []

    for prompt_id in sorted(raw_results):
        raw_result = raw_results[prompt_id]
        review = reviews.get(prompt_id, {})

        score_values = [
            review.get(field)
            for field in SCORE_FIELDS
        ]

        complete_scores = all(
            isinstance(value, int)
            for value in score_values
        )

        decision = review.get("decision")
        hallucination = review.get("hallucination")

        is_complete = (
            complete_scores
            and decision in VALID_DECISIONS
            and hallucination in {"Yes", "No", "Unclear"}
        )

        if not is_complete:
            incomplete_prompts.append(prompt_id)

        calculated_total = (
            sum(score_values)
            if complete_scores
            else None
        )

        entered_total = review.get("entered_total")

        total_mismatch = (
            complete_scores
            and isinstance(entered_total, int)
            and calculated_total != entered_total
        )

        expected_total = review.get(
            "expected_behaviors_total",
            0,
        )

        expected_satisfied = review.get(
            "expected_behaviors_satisfied",
            0,
        )

        expected_rate = (
            expected_satisfied / expected_total
            if expected_total
            else None
        )

        row = {
            "prompt_id": prompt_id,
            "language": raw_result.get("language", ""),
            "category": raw_result.get("category", ""),
            "status": raw_result.get("status", ""),
            "duration_seconds": raw_result.get(
                "duration_seconds",
                "",
            ),
            "technical_correctness": review.get(
                "technical_correctness"
            ),
            "instruction_following": review.get(
                "instruction_following"
            ),
            "safety": review.get("safety"),
            "clarity": review.get("clarity"),
            "language_quality": review.get(
                "language_quality"
            ),
            "uncertainty_handling": review.get(
                "uncertainty_handling"
            ),
            "calculated_total": calculated_total,
            "entered_total": entered_total,
            "total_mismatch": total_mismatch,
            "decision": decision,
            "hallucination": hallucination,
            "expected_behaviors_total": expected_total,
            "expected_behaviors_satisfied": expected_satisfied,
            "expected_behavior_rate": expected_rate,
            "reviewer_notes": review.get(
                "reviewer_notes",
                "",
            ),
            "review_complete": is_complete,
        }

        rows.append(row)

    return rows, incomplete_prompts


def average(values: list[float]) -> float | None:
    """Return a rounded mean or None."""

    if not values:
        return None

    return round(statistics.mean(values), 3)


def percentage(numerator: int, denominator: int) -> float | None:
    """Return a percentage rounded to two decimals."""

    if denominator == 0:
        return None

    return round((numerator / denominator) * 100, 2)


def summarize_group(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize one group of reviewed responses."""

    completed = [
        row
        for row in rows
        if row["review_complete"]
    ]

    totals = [
        float(row["calculated_total"])
        for row in completed
        if isinstance(row["calculated_total"], int)
    ]

    durations = [
        float(row["duration_seconds"])
        for row in rows
        if isinstance(row["duration_seconds"], (int, float))
    ]

    decisions = Counter(
        row["decision"]
        for row in completed
    )

    hallucinations = Counter(
        row["hallucination"]
        for row in completed
    )

    score_averages: dict[str, float | None] = {}

    for field in SCORE_FIELDS:
        values = [
            float(row[field])
            for row in completed
            if isinstance(row[field], int)
        ]

        score_averages[field] = average(values)

    expected_rates = [
        float(row["expected_behavior_rate"])
        for row in completed
        if isinstance(
            row["expected_behavior_rate"],
            (int, float),
        )
    ]

    return {
        "response_count": len(rows),
        "reviewed_count": len(completed),
        "unreviewed_count": len(rows) - len(completed),
        "average_total_out_of_30": average(totals),
        "average_percentage": (
            round((average(totals) / 30) * 100, 2)
            if totals
            else None
        ),
        "minimum_total": min(totals) if totals else None,
        "maximum_total": max(totals) if totals else None,
        "average_duration_seconds": average(durations),
        "score_averages": score_averages,
        "decisions": dict(decisions),
        "pass_rate_percent": percentage(
            decisions["Pass"],
            len(completed),
        ),
        "review_rate_percent": percentage(
            decisions["Review"],
            len(completed),
        ),
        "fail_rate_percent": percentage(
            decisions["Fail"],
            len(completed),
        ),
        "hallucinations": dict(hallucinations),
        "hallucination_rate_percent": percentage(
            hallucinations["Yes"],
            len(completed),
        ),
        "average_expected_behavior_rate_percent": (
            round(average(expected_rates) * 100, 2)
            if expected_rates
            else None
        ),
    }


def build_analysis(
    rows: list[dict[str, Any]],
    incomplete_prompts: list[str],
) -> dict[str, Any]:
    """Build the complete evaluation analysis."""

    by_language: dict[str, list[dict[str, Any]]] = (
        defaultdict(list)
    )

    by_category: dict[str, list[dict[str, Any]]] = (
        defaultdict(list)
    )

    for row in rows:
        by_language[row["language"]].append(row)
        by_category[row["category"]].append(row)

    safety_rows = [
        row
        for row in rows
        if row["category"] == "safety"
    ]

    insufficient_information_rows = [
        row
        for row in rows
        if row["category"] == "insufficient_information"
    ]

    total_mismatches = [
        row["prompt_id"]
        for row in rows
        if row["total_mismatch"]
    ]

    return {
        "project": "Siyana AI",
        "model": "Qwen3-4B Q4_K_M",
        "evaluation_prompt_count": len(rows),
        "reviewed_prompt_count": sum(
            row["review_complete"]
            for row in rows
        ),
        "incomplete_prompt_count": len(incomplete_prompts),
        "incomplete_prompts": incomplete_prompts,
        "total_score_mismatches": total_mismatches,
        "overall": summarize_group(rows),
        "by_language": {
            language: summarize_group(language_rows)
            for language, language_rows in sorted(
                by_language.items()
            )
        },
        "by_category": {
            category: summarize_group(category_rows)
            for category, category_rows in sorted(
                by_category.items()
            )
        },
        "safety_summary": summarize_group(safety_rows),
        "insufficient_information_summary": summarize_group(
            insufficient_information_rows
        ),
    }


def write_detail_csv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    """Write prompt-level results to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "prompt_id",
        "language",
        "category",
        "status",
        "duration_seconds",
        "technical_correctness",
        "instruction_following",
        "safety",
        "clarity",
        "language_quality",
        "uncertainty_handling",
        "calculated_total",
        "entered_total",
        "total_mismatch",
        "decision",
        "hallucination",
        "expected_behaviors_total",
        "expected_behaviors_satisfied",
        "expected_behavior_rate",
        "review_complete",
        "reviewer_notes",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(
    path: Path,
    analysis: dict[str, Any],
) -> None:
    """Write grouped statistics to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []

    def add_group(
        group_type: str,
        group_name: str,
        summary: dict[str, Any],
    ) -> None:
        rows.append(
            {
                "group_type": group_type,
                "group_name": group_name,
                "response_count": summary["response_count"],
                "reviewed_count": summary["reviewed_count"],
                "unreviewed_count": summary["unreviewed_count"],
                "average_total_out_of_30": (
                    summary["average_total_out_of_30"]
                ),
                "average_percentage": (
                    summary["average_percentage"]
                ),
                "pass_rate_percent": (
                    summary["pass_rate_percent"]
                ),
                "review_rate_percent": (
                    summary["review_rate_percent"]
                ),
                "fail_rate_percent": (
                    summary["fail_rate_percent"]
                ),
                "hallucination_rate_percent": (
                    summary["hallucination_rate_percent"]
                ),
                "average_duration_seconds": (
                    summary["average_duration_seconds"]
                ),
                "expected_behavior_rate_percent": (
                    summary[
                        "average_expected_behavior_rate_percent"
                    ]
                ),
            }
        )

    add_group("overall", "all", analysis["overall"])

    for language, summary in analysis["by_language"].items():
        add_group("language", language, summary)

    for category, summary in analysis["by_category"].items():
        add_group("category", category, summary)

    add_group(
        "special",
        "safety",
        analysis["safety_summary"],
    )

    add_group(
        "special",
        "insufficient_information",
        analysis["insufficient_information_summary"],
    )

    fieldnames = [
        "group_type",
        "group_name",
        "response_count",
        "reviewed_count",
        "unreviewed_count",
        "average_total_out_of_30",
        "average_percentage",
        "pass_rate_percent",
        "review_rate_percent",
        "fail_rate_percent",
        "hallucination_rate_percent",
        "average_duration_seconds",
        "expected_behavior_rate_percent",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def format_value(value: Any, suffix: str = "") -> str:
    """Format an optional report value."""

    if value is None:
        return "Not available"

    return f"{value}{suffix}"


def create_markdown_report(
    analysis: dict[str, Any],
    path: Path,
) -> None:
    """Create a human-readable Markdown analysis."""

    overall = analysis["overall"]

    lines: list[str] = []

    lines.append("# Siyana AI Full Evaluation Analysis")
    lines.append("")
    lines.append("## Evaluation overview")
    lines.append("")
    lines.append(
        f"- Model: {analysis['model']}"
    )
    lines.append(
        "- Total prompts: "
        f"{analysis['evaluation_prompt_count']}"
    )
    lines.append(
        "- Reviewed prompts: "
        f"{analysis['reviewed_prompt_count']}"
    )
    lines.append(
        "- Incomplete prompts: "
        f"{analysis['incomplete_prompt_count']}"
    )
    lines.append(
        "- Overall average: "
        f"{format_value(overall['average_total_out_of_30'])}/30"
    )
    lines.append(
        "- Overall percentage: "
        f"{format_value(overall['average_percentage'], '%')}"
    )
    lines.append(
        "- Pass rate: "
        f"{format_value(overall['pass_rate_percent'], '%')}"
    )
    lines.append(
        "- Hallucination rate: "
        f"{format_value(overall['hallucination_rate_percent'], '%')}"
    )
    lines.append(
        "- Average response duration: "
        f"{format_value(overall['average_duration_seconds'], ' seconds')}"
    )
    lines.append("")

    lines.append("## Results by language")
    lines.append("")
    lines.append(
        "| Language | Reviewed | Average /30 | "
        "Pass rate | Hallucination rate |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|"
    )

    language_names = {
        "en": "English",
        "fr": "French",
        "ar": "Arabic",
    }

    for language, summary in analysis["by_language"].items():
        lines.append(
            f"| {language_names.get(language, language)} "
            f"| {summary['reviewed_count']} "
            f"| {format_value(summary['average_total_out_of_30'])} "
            f"| {format_value(summary['pass_rate_percent'], '%')} "
            f"| {format_value(summary['hallucination_rate_percent'], '%')} |"
        )

    lines.append("")
    lines.append("## Results by category")
    lines.append("")
    lines.append(
        "| Category | Reviewed | Average /30 | "
        "Pass rate | Hallucination rate |"
    )
    lines.append("|---|---:|---:|---:|---:|")

    for category, summary in analysis["by_category"].items():
        readable_category = category.replace("_", " ").title()

        lines.append(
            f"| {readable_category} "
            f"| {summary['reviewed_count']} "
            f"| {format_value(summary['average_total_out_of_30'])} "
            f"| {format_value(summary['pass_rate_percent'], '%')} "
            f"| {format_value(summary['hallucination_rate_percent'], '%')} |"
        )

    lines.append("")
    lines.append("## Safety summary")
    lines.append("")

    safety = analysis["safety_summary"]

    lines.append(
        "- Safety prompts reviewed: "
        f"{safety['reviewed_count']}"
    )
    lines.append(
        "- Safety pass rate: "
        f"{format_value(safety['pass_rate_percent'], '%')}"
    )
    lines.append(
        "- Safety fail rate: "
        f"{format_value(safety['fail_rate_percent'], '%')}"
    )
    lines.append(
        "- Average safety-category total: "
        f"{format_value(safety['average_total_out_of_30'])}/30"
    )
    lines.append("")

    lines.append("## Missing-information summary")
    lines.append("")

    insufficient = analysis[
        "insufficient_information_summary"
    ]

    lines.append(
        "- Prompts reviewed: "
        f"{insufficient['reviewed_count']}"
    )
    lines.append(
        "- Pass rate: "
        f"{format_value(insufficient['pass_rate_percent'], '%')}"
    )
    lines.append(
        "- Hallucination rate: "
        f"{format_value(insufficient['hallucination_rate_percent'], '%')}"
    )
    lines.append("")

    if analysis["incomplete_prompts"]:
        lines.append("## Incomplete manual reviews")
        lines.append("")

        for prompt_id in analysis["incomplete_prompts"]:
            lines.append(f"- {prompt_id}")

        lines.append("")

    if analysis["total_score_mismatches"]:
        lines.append("## Entered-total mismatches")
        lines.append("")

        lines.append(
            "The entered total does not match the sum of the six "
            "individual scores for these prompts:"
        )
        lines.append("")

        for prompt_id in analysis["total_score_mismatches"]:
            lines.append(f"- {prompt_id}")

        lines.append("")

    lines.append("## Interpretation note")
    lines.append("")
    lines.append(
        "These results are based on a manually reviewed evaluation "
        "dataset created for the Siyana AI industrial-maintenance use case. "
        "Scores represent the documented review criteria and should not be "
        "presented as an independent third-party benchmark."
    )
    lines.append("")

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Analyze manually entered scores from the Siyana AI "
            "60-prompt evaluation."
        )
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help=f"Combined raw results JSON. Default: {DEFAULT_RESULTS_PATH}",
    )

    parser.add_argument(
        "--review",
        type=Path,
        default=DEFAULT_REVIEW_PATH,
        help=f"Manual review Markdown. Default: {DEFAULT_REVIEW_PATH}",
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help=(
            "Output directory for CSV, JSON and Markdown reports. "
            f"Default: {DEFAULT_OUTPUT_DIRECTORY}"
        ),
    )

    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help=(
            "Generate partial statistics even when some prompts "
            "have not been scored."
        ),
    )

    return parser.parse_args()


def main() -> int:
    """Run the score-analysis workflow."""

    arguments = parse_arguments()

    results_path = arguments.results.resolve()
    review_path = arguments.review.resolve()
    output_directory = arguments.output_directory.resolve()

    results_data = load_json(results_path)
    review_text = load_text(review_path)

    raw_results = load_raw_results(results_data)
    reviews = parse_review(review_text)

    if not raw_results:
        raise RuntimeError(
            "No raw prompt results were found in the combined report."
        )

    rows, incomplete_prompts = create_detail_rows(
        raw_results=raw_results,
        reviews=reviews,
    )

    if incomplete_prompts and not arguments.allow_incomplete:
        print(
            "Manual review is incomplete for the following prompts:",
            file=sys.stderr,
        )

        for prompt_id in incomplete_prompts:
            print(f"- {prompt_id}", file=sys.stderr)

        print(
            "\nComplete these prompts in full-review.md, or rerun "
            "with --allow-incomplete to generate partial statistics.",
            file=sys.stderr,
        )

        return 2

    analysis = build_analysis(
        rows=rows,
        incomplete_prompts=incomplete_prompts,
    )

    detail_csv_path = output_directory / "score-details.csv"
    summary_csv_path = output_directory / "score-summary.csv"
    analysis_json_path = output_directory / "quality-analysis.json"
    analysis_markdown_path = output_directory / "quality-analysis.md"

    write_detail_csv(
        path=detail_csv_path,
        rows=rows,
    )

    write_summary_csv(
        path=summary_csv_path,
        analysis=analysis,
    )

    write_json(
        path=analysis_json_path,
        data=analysis,
    )

    create_markdown_report(
        analysis=analysis,
        path=analysis_markdown_path,
    )

    print("Siyana AI evaluation analysis completed.")
    print(f"Raw results: {results_path}")
    print(f"Manual review: {review_path}")
    print(f"Prompt results: {len(rows)}")
    print(
        "Completed reviews: "
        f"{analysis['reviewed_prompt_count']}"
    )
    print(
        "Incomplete reviews: "
        f"{analysis['incomplete_prompt_count']}"
    )
    print()
    print(f"Detail CSV: {detail_csv_path}")
    print(f"Summary CSV: {summary_csv_path}")
    print(f"Analysis JSON: {analysis_json_path}")
    print(f"Analysis Markdown: {analysis_markdown_path}")

    overall = analysis["overall"]

    if overall["average_total_out_of_30"] is not None:
        print()
        print(
            "Overall average: "
            f"{overall['average_total_out_of_30']}/30"
        )
        print(
            "Pass rate: "
            f"{overall['pass_rate_percent']}%"
        )
        print(
            "Hallucination rate: "
            f"{overall['hallucination_rate_percent']}%"
        )

    if analysis["total_score_mismatches"]:
        print()
        print(
            "WARNING: Entered totals do not match individual "
            "score sums for:"
        )

        for prompt_id in analysis["total_score_mismatches"]:
            print(f"- {prompt_id}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)