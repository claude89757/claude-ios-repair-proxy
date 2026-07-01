---
name: claude-ios-release
description: Use when this repository needs a manual public version release, semantic version tag, or GitHub Release after production has already deployed successfully.
---

# Claude iOS Release

Use this skill to publish a deliberate `vX.Y.Z` GitHub Release for this project. Do not use it for normal production deploys; `Deploy production` remains the deploy path.

## Rules

- Release only commits already deployed by `Deploy production`.
- Confirm `/opt/claude-ios-repair/REVISION` equals the target SHA before publishing.
- Use SemVer tags only: `vMAJOR.MINOR.PATCH`.
- Do not create or move tags manually. Trigger `.github/workflows/release-version.yml`.
- Do not use moving tags such as `latest`, `stable`, or `prod`.
- Never print secrets from `_private/`.

## Workflow

1. Resolve the requested version and target ref.
   ```bash
   python .agents/skills/claude-ios-release/scripts/release_preflight.py v0.1.0
   git fetch origin --tags
   git rev-parse <target-ref>^{commit}
   ```
2. Require a clean repository and local `main` equal to `origin/main`.
3. Verify the latest successful `Deploy production` run uses the target SHA.
   ```bash
   gh run list --repo claude89757/claude-ios-repair-proxy --workflow "Deploy production" --branch main --status success --limit 1 --json databaseId,headSha,status,conclusion,url
   ```
4. Verify production revision over SSH using `claude-ios-repair-ops`; the output SHA must equal the target SHA.
5. Preview release notes.
   ```bash
   python .agents/skills/claude-ios-release/scripts/build_release_notes.py v0.1.0 --target-sha <sha> --output /tmp/claude-ios-release-notes.md
   ```
6. Restate the exact version, SHA, latest deploy run, and production revision. Ask for final confirmation before publishing.
7. Trigger the release workflow.
   ```bash
   gh workflow run "Release version" \
     --repo claude89757/claude-ios-repair-proxy \
     --ref main \
     -f version=v0.1.0 \
     -f target_ref=<sha> \
     -f dry_run=false
   ```
8. Watch the workflow and verify the tag and GitHub Release.
   ```bash
   gh run watch <run-id> --repo claude89757/claude-ios-repair-proxy --exit-status
   git fetch origin --tags
   git rev-parse v0.1.0^{commit}
   gh release view v0.1.0 --repo claude89757/claude-ios-repair-proxy
   ```

## Version Choice

- First public marker: `v0.1.0`.
- User-visible feature batch: increment minor.
- Fixes, copy, styles, release-process changes: increment patch.
- Breaking public behavior after `v1.0.0`: increment major.
