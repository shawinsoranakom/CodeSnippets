def test_dry_run_then_real_run_match(self, git_repo: Path):
        """T014: Dry-run name matches subsequent real creation."""
        (git_repo / "specs" / "001-existing").mkdir(parents=True)
        # Dry-run first
        dry_result = run_script(
            git_repo, "--dry-run", "--short-name", "match-test", "Match test"
        )
        assert dry_result.returncode == 0, dry_result.stderr
        dry_branch = None
        for line in dry_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                dry_branch = line.split(":", 1)[1].strip()
        # Real run
        real_result = run_script(
            git_repo, "--short-name", "match-test", "Match test"
        )
        assert real_result.returncode == 0, real_result.stderr
        real_branch = None
        for line in real_result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                real_branch = line.split(":", 1)[1].strip()
        assert dry_branch == real_branch, f"dry={dry_branch} != real={real_branch}"