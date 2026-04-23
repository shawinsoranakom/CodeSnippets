def test_dry_run_with_timestamp(self, git_repo: Path):
        """T017: Dry-run works with --timestamp flag."""
        result = run_script(
            git_repo, "--dry-run", "--timestamp", "--short-name", "ts-feat", "Timestamp feature"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch is not None, "no BRANCH_NAME in output"
        assert re.match(r"^\d{8}-\d{6}-ts-feat$", branch), f"unexpected: {branch}"
        # Verify no side effects
        branches = subprocess.run(
            ["git", "branch", "--list", f"*ts-feat*"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert branches.returncode == 0, f"'git branch --list' failed: {branches.stderr}"
        assert branches.stdout.strip() == ""