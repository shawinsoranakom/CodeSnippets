def test_run_starter_project_no_import_errors(self, template_file):
        """Test that starter project can be loaded without langflow or lfx import errors.

        We expect execution errors (missing API keys, missing inputs, etc.)
        but there should be NO errors about importing langflow or lfx modules.
        """
        # Run the command with --no-check-variables to skip variable validation
        # Use verbose mode to get detailed error messages in stderr
        result = runner.invoke(
            app,
            ["run", "--verbose", "--no-check-variables", str(template_file), "test input"],
        )

        # The command will likely fail due to missing API keys, etc.
        # But we're checking that there are no import errors

        # Use the combined output provided by Click/Typer
        all_output = result.output

        # Check for import errors related to langflow or lfx
        if "ModuleNotFoundError" in all_output or "ImportError" in all_output or "Module" in all_output:
            # Check for langflow import errors
            if "No module named 'langflow'" in all_output or "Module langflow" in all_output:
                # Extract the specific error for better debugging
                error_line = ""
                for line in all_output.split("\n"):
                    if "langflow" in line and ("No module named" in line or "Module" in line):
                        error_line = line.strip()
                        break
                pytest.fail(f"Langflow import error found in {template_file.name}.\nError: {error_line}")

            # Check for lfx import errors (these indicate structural issues)
            if "No module named 'lfx." in all_output or "Module lfx." in all_output:
                # Extract the specific error for better debugging
                import re

                # Remove ANSI color codes for cleaner output
                clean_output = re.sub(r"\x1b\[[0-9;]*m", "", all_output)

                error_lines = []
                for line in clean_output.split("\n"):
                    if "lfx" in line and ("No module named" in line or "Module lfx." in line):
                        # Extract just the module name from various error formats
                        if "No module named" in line:
                            match = re.search(r"No module named ['\"]([^'\"]+)['\"]", line)
                            if match:
                                error_lines.append(f"  - Missing module: {match.group(1)}")
                        elif "Module lfx." in line and "not found" in line:
                            match = re.search(r"Module (lfx\.[^\s]+)", line)
                            if match:
                                error_lines.append(f"  - Missing module: {match.group(1)}")

                # Deduplicate while preserving order
                seen = set()
                unique_errors = []
                for error in error_lines:
                    if error not in seen:
                        seen.add(error)
                        unique_errors.append(error)

                error_detail = "\n".join(unique_errors[:5])  # Show first 5 unique lfx errors
                pytest.fail(
                    f"LFX import error found in {template_file.name}.\n"
                    f"This indicates lfx internal structure issues.\n"
                    f"Missing modules:\n{error_detail}"
                )

            # Check for other critical import errors
            if "cannot import name" in all_output and ("langflow" in all_output or "lfx" in all_output):
                # Extract the specific import error
                error_line = ""
                for line in all_output.split("\n"):
                    if "cannot import name" in line:
                        error_line = line.strip()
                        break
                pytest.fail(f"Import error found in {template_file.name}.\nError: {error_line}")