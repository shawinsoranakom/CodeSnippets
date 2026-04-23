def main():
    """
    Main entry point for the RTL/LTR Markdown linter.

    Parses command-line arguments, loads configuration, and scans the specified files or directories
    for Markdown files. For each file, it detects RTL/LTR issues and writes all findings to a log file.
    For files changed in the current PR, only issues on changed lines are printed to stdout as GitHub
    Actions annotations.

    Exit code is 1 if any error or warning is found on changed lines, otherwise 0.

    Command-line arguments:
        paths_to_scan: List of files or directories to scan for issues.
        --changed-files: List of files changed in the PR (for annotation filtering).
        --log-file: Path to the output log file (default: rtl-linter-output.log).
    """
    # Create an ArgumentParser object to handle command-line arguments
    parser = argparse.ArgumentParser(
        description="Lints Markdown files for RTL/LTR issues, with PR annotation support."
    )

    # Argument for files/directories to scan
    parser.add_argument(
        'paths_to_scan',
        nargs='+',
        help="List of files or directories to scan for all issues."
    )

    # Optional argument for changed files (for PR annotation filtering)
    parser.add_argument(
        '--changed-files',
        nargs='*',
        default=None,
        help="List of changed files to generate PR annotations for."
    )

    # Optional argument for the log file path
    parser.add_argument(
        '--log-file',
        default='rtl-linter-output.log',
        help="File to write all linter output to."
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Determine the directory where the script is located to find the config file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Load the configuration from 'rtl_linter_config.yml'
    cfg = load_config(os.path.join(script_dir, 'rtl_linter_config.yml'))

    # Initialize counters for total files processed and errors/warnings found
    total = errs = 0

    # Count errors/warnings ONLY on changed/added lines for PR annotation exit code
    annotated_errs = 0

    # Normalize changed file paths for consistent comparison
    changed_files_set = set(os.path.normpath(f) for f in args.changed_files) if args.changed_files else set()

    # Build a map: {filepath: set(line_numbers)} for changed files
    changed_lines_map = {}
    for f in changed_files_set:
        changed_lines_map[f] = get_changed_lines_for_file(f)

    # Flag to check if any issues were found
    any_issues = False

    # Open the specified log file in write mode with UTF-8 encoding
    with open(args.log_file, 'w', encoding='utf-8') as log_f:

        # Iterate over each path provided in 'paths_to_scan'
        for p_scan_arg in args.paths_to_scan:

            # Normalize the scan path to ensure consistent handling (e.g., slashes)
            normalized_scan_path = os.path.normpath(p_scan_arg)

            # If the path is a directory, recursively scan for .md files
            if os.path.isdir(normalized_scan_path):

                # Walk through the directory and its subdirectories to find all Markdown files
                for root, _, files in os.walk(normalized_scan_path):

                    # For each file in the directory
                    for fn in files:

                        # If the file is a Markdown file, lint it
                        if fn.lower().endswith('.md'):
                            file_path = os.path.normpath(os.path.join(root, fn))
                            total += 1
                            issues_found = lint_file(file_path, cfg)

                            # Process each issue found
                            for issue_str in issues_found:
                                log_f.write(issue_str + '\n')
                                any_issues = True # Flag to check if any issues were found

                                # For GitHub Actions PR annotations: print only if the file is changed
                                # and the issue is on a line that was actually modified or added in the PR
                                if file_path in changed_files_set:
                                    m = re.search(r'line=(\d+)', issue_str)
                                    if m and int(m.group(1)) in changed_lines_map.get(file_path, set()):
                                        print(issue_str)

                                        # Count errors on changed lines for the exit code logic
                                        if issue_str.startswith("::error"):
                                            annotated_errs += 1

                                # Count all errors/warnings for reporting/debugging purposes
                                if issue_str.startswith("::error") or issue_str.startswith("::warning"):
                                    errs += 1

            # If the path is a Markdown file, lint it directly
            elif normalized_scan_path.lower().endswith('.md'):
                total += 1
                issues_found = lint_file(normalized_scan_path, cfg)

                # Process each issue found
                for issue_str in issues_found:

                    # Always write the issue to the log file for full reporting
                    log_f.write(issue_str + '\n')
                    any_issues = True # Flag to check if any issues were found

                    # For GitHub Actions PR annotations: print only if the file is changed
                    # and the issue is on a line that was actually modified or added in the PR
                    if normalized_scan_path in changed_files_set:

                        # Extract the line number from the issue string (e.g., ...line=123::)
                        m = re.search(r'line=(\d+)', issue_str)

                        if m and int(m.group(1)) in changed_lines_map.get(normalized_scan_path, set()):

                            # For GitHub Actions PR annotations: print the annotation
                            # so that GitHub Actions can display it in the PR summary
                            print(issue_str)

                            # Count errors on changed lines for the exit code logic
                            if issue_str.startswith("::error"):
                                annotated_errs += 1

                    # Count all errors/warnings for reporting/debugging purposes
                    if issue_str.startswith("::error") or issue_str.startswith("::warning"):
                        errs += 1

    # If no issues were found, remove the log file
    if not any_issues:
        try:
            os.remove(args.log_file)
        except Exception:
            pass

    # Print a debug message to stderr summarizing the linting process
    print(f"::notice ::Processed {total} files, found {errs} issues.")

    # Exit code: 1 only if there are annotated errors/warnings on changed lines
    sys.exit(1 if annotated_errs else 0)