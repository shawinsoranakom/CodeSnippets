def test_print_sampled_stats_sort_by_name(self):
        """Test sort by function name option."""

        with io.StringIO() as output:
            with mock.patch("sys.stdout", output):
                print_sampled_stats(
                    self.mock_stats, sort=-1, sample_interval_usec=100
                )  # sort by name

            result = output.getvalue()
            lines = result.strip().split("\n")

        # Find the data lines (skip header and summary)
        # Data lines start with whitespace and numbers, and contain filename:lineno(function)
        data_lines = []
        for line in lines:
            # Skip header lines and summary sections
            if (
                line.startswith("     ")
                and "(" in line
                and ")" in line
                and not line.startswith(
                    "     1."
                )  # Skip summary lines that start with times
                and not line.startswith(
                    "     0."
                )  # Skip summary lines that start with times
                and not "per call" in line  # Skip summary lines
                and not "calls" in line  # Skip summary lines
                and not "total time" in line  # Skip summary lines
                and not "cumulative time" in line
            ):  # Skip summary lines
                data_lines.append(line)

        # Extract just the function names for comparison
        func_names = []

        for line in data_lines:
            # Function name is between the last ( and ), accounting for ANSI color codes
            match = re.search(r"\(([^)]+)\)$", line)
            if match:
                func_name = match.group(1)
                # Remove ANSI color codes
                func_name = re.sub(r"\x1b\[[0-9;]*m", "", func_name)
                func_names.append(func_name)

        # Verify we extracted function names and they are sorted
        self.assertGreater(
            len(func_names), 0, "Should have extracted some function names"
        )
        self.assertEqual(
            func_names,
            sorted(func_names),
            f"Function names {func_names} should be sorted alphabetically",
        )