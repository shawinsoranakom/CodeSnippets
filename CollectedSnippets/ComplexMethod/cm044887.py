def test_dry_run_no_git(self, no_git_dir: Path):
        """T019: Dry-run works in non-git directory."""
        (no_git_dir / "specs" / "001-existing").mkdir(parents=True)
        result = run_script(
            no_git_dir, "--dry-run", "--short-name", "no-git-dry", "No git dry run"
        )
        assert result.returncode == 0, result.stderr
        branch = None
        for line in result.stdout.splitlines():
            if line.startswith("BRANCH_NAME:"):
                branch = line.split(":", 1)[1].strip()
        assert branch == "002-no-git-dry", f"expected 002-no-git-dry, got: {branch}"
        # Verify no spec dir created
        spec_dirs = [
            d.name
            for d in (no_git_dir / "specs").iterdir()
            if d.is_dir() and "no-git-dry" in d.name
        ]
        assert len(spec_dirs) == 0