from pathlib import Path
import importlib.util
import pytest


ACTIONS = Path(".github/workflows")
RELEASE_SKILL = Path(".agents/skills/claude-ios-release")


def load_release_script(name: str):
    path = RELEASE_SKILL / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_workflow_is_manual_and_does_not_deploy_production():
    workflow = (ACTIONS / "release-version.yml").read_text()

    assert "name: Release version" in workflow
    assert "workflow_dispatch:" in workflow
    assert "version:" in workflow
    assert "target_ref:" in workflow
    assert "dry_run:" in workflow
    assert "push:" not in workflow
    assert "pull_request:" not in workflow

    assert "permissions:" in workflow
    assert "contents: write" in workflow
    assert "actions: read" in workflow
    assert "environment: production" not in workflow
    assert "PROD_SSH_PRIVATE_KEY" not in workflow
    assert "scp " not in workflow
    assert "systemctl restart" not in workflow


def test_release_workflow_checks_deployed_commit_before_creating_tag():
    workflow = (ACTIONS / "release-version.yml").read_text()

    assert "fetch-depth: 0" in workflow
    assert "git fetch --tags --force" in workflow
    assert "python -m pytest" in workflow
    assert "Deploy production" in workflow
    assert "gh run list" in workflow
    assert "LATEST_DEPLOY_SHA" in workflow
    assert 'git tag -a "$VERSION" "$TARGET_SHA"' in workflow
    assert 'git push origin "$VERSION"' in workflow
    assert "gh release create" in workflow
    assert "release-notes.md" in workflow
    assert "if: ${{ inputs.dry_run != true }}" in workflow
    assert workflow.index("python -m pytest") < workflow.index('git tag -a "$VERSION" "$TARGET_SHA"')


def test_release_skill_contains_safe_manual_version_release_workflow():
    skill = (RELEASE_SKILL / "SKILL.md").read_text()
    agent = (RELEASE_SKILL / "agents" / "openai.yaml").read_text()

    assert "name: claude-ios-release" in skill
    assert "Use when" in skill
    assert "vX.Y.Z" in skill
    assert "release-version.yml" in skill
    assert "Deploy production" in skill
    assert "/opt/claude-ios-repair/REVISION" in skill
    assert "Do not create or move tags manually" in skill
    assert "release_preflight.py" in skill
    assert "build_release_notes.py" in skill
    assert "display_name: \"Claude iOS Release\"" in agent
    assert "default_prompt: \"Use $claude-ios-release" in agent


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.1.0", "v0.1.0"),
        ("v0.1.0", "v0.1.0"),
        ("  v12.34.56  ", "v12.34.56"),
    ],
)
def test_release_preflight_normalizes_semver_versions(raw, expected):
    preflight = load_release_script("release_preflight.py")

    assert preflight.normalize_version(raw) == expected


@pytest.mark.parametrize("raw", ["v1.2", "v1.2.3.4", "v01.2.3", "latest", "prod-2026-07-01"])
def test_release_preflight_rejects_non_semver_versions(raw):
    preflight = load_release_script("release_preflight.py")

    with pytest.raises(ValueError):
        preflight.normalize_version(raw)


def test_release_notes_builder_summarizes_commit_subjects():
    notes = load_release_script("build_release_notes.py")
    commits = [
        {"sha": "d06f3d06b95a", "subject": "Add repair completion modal"},
        {"sha": "1dfb3ef7a4eb", "subject": "Refine public entry UI"},
    ]

    body = notes.render_release_notes(
        version="v0.1.0",
        target_sha="d06f3d06b95a867b73a79e8fe196d650643c4826",
        previous_tag="",
        commits=commits,
    )

    assert body.startswith("## v0.1.0")
    assert "Target commit: `d06f3d06b95a867b73a79e8fe196d650643c4826`" in body
    assert "- d06f3d0 Add repair completion modal" in body
    assert "- 1dfb3ef Refine public entry UI" in body
