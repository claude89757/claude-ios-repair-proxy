#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def short_sha(value: str) -> str:
    return value[:7]


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def latest_version_tag() -> str:
    tags = run_git(["tag", "--list", "v[0-9]*", "--sort=-version:refname"])
    return tags.splitlines()[0] if tags else ""


def collect_commits(previous_tag: str, target_sha: str) -> list[dict[str, str]]:
    revision_range = f"{previous_tag}..{target_sha}" if previous_tag else target_sha
    output = run_git(["log", "--pretty=format:%H%x00%s", revision_range])
    commits = []
    for line in output.splitlines():
        if not line:
            continue
        sha, subject = line.split("\x00", 1)
        commits.append({"sha": sha, "subject": subject})
    return commits


def render_release_notes(
    *,
    version: str,
    target_sha: str,
    previous_tag: str,
    commits: list[dict[str, str]],
) -> str:
    previous = previous_tag or "none"
    lines = [
        f"## {version}",
        "",
        f"Target commit: `{target_sha}`",
        f"Previous tag: `{previous}`",
        "",
        "### Changes",
    ]

    if commits:
        for commit in commits:
            lines.append(f"- {short_sha(commit['sha'])} {commit['subject']}")
    else:
        lines.append("- No commits found in the selected range.")

    lines.extend(
        [
            "",
            "### Verification",
            "- Release workflow runs the full test suite before creating the tag.",
            "- The target commit must match the latest successful Deploy production run.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build release notes for a Claude iOS release.")
    parser.add_argument("version", help="Release version, for example v0.1.0")
    parser.add_argument("--target-sha", required=True, help="Target commit SHA for the release")
    parser.add_argument("--previous-tag", default="", help="Previous release tag; defaults to latest v* tag")
    parser.add_argument("--output", required=True, help="Path to write release notes")
    args = parser.parse_args()

    previous_tag = args.previous_tag or latest_version_tag()
    commits = collect_commits(previous_tag, args.target_sha)
    body = render_release_notes(
        version=args.version,
        target_sha=args.target_sha,
        previous_tag=previous_tag,
        commits=commits,
    )
    Path(args.output).write_text(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
