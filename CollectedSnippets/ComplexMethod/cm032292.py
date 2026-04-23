def build_pytest_command(self) -> List[str]:
        """Build the pytest command arguments"""
        cmd = ["pytest", str(self.ut_dir)]

        # Add test path

        # Add markers
        if self.markers:
            cmd.extend(["-m", self.markers])

        # Add verbose flag
        if self.verbose:
            cmd.extend(["-vv"])
        else:
            cmd.append("-v")

        # Add coverage
        if self.coverage:
            # Relative path from test directory to source code
            source_path = str(self.project_root / "common")
            cmd.extend([
                "--cov", source_path,
                "--cov-report", "html",
                "--cov-report", "term"
            ])

        # Add parallel execution
        if self.parallel:
            # Try to get number of CPU cores
            try:
                import multiprocessing
                cpu_count = multiprocessing.cpu_count()
                cmd.extend(["-n", str(cpu_count)])
            except ImportError:
                # Fallback to auto if multiprocessing not available
                cmd.extend(["-n", "auto"])

        # Add ignore syntax warning
        if self.ignore_syntax_warning:
            cmd.extend(["-W", "ignore::SyntaxWarning"])

        # Add default options from pyproject.toml if it exists
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            cmd.extend(["--config-file", str(pyproject_path)])

        return cmd