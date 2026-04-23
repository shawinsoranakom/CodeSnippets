def _eval_python(
        self,
        result: ChallengeResult,
        challenge: Challenge,
        target_files: list[str],
    ) -> float:
        """Run Python test file and check output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Copy output files
            for filepath, content in result.output_files.items():
                dest = tmpdir_path / filepath
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content)

            # Copy custom test file if exists
            custom_python = challenge.artifacts_dir / "custom_python"
            if custom_python.exists():
                for item in custom_python.iterdir():
                    if item.is_file():
                        shutil.copy2(item, tmpdir_path / item.name)

            # Run the test file(s)
            for target in target_files:
                test_file = tmpdir_path / target
                if test_file.exists() and test_file.suffix == ".py":
                    proc = subprocess.run(
                        [sys.executable, str(test_file)],
                        cwd=str(tmpdir_path),
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if proc.returncode != 0:
                        return 0.0
                    if "error" in proc.stderr.lower():
                        return 0.0

        return 1.0