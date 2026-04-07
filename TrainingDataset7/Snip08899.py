def run_formatters(written_files, black_path=(sentinel := object()), stderr=sys.stderr):
    """
    Run the black formatter on the specified files.
    """
    # Use a sentinel rather than None, as which() returns None when not found.
    if black_path is sentinel:
        black_path = shutil.which("black")
    if black_path:
        try:
            subprocess.run(
                [black_path, "--fast", "--", *written_files],
                capture_output=True,
            )
        except OSError:
            stderr.write("Formatters failed to launch:")
            traceback.print_exc(file=stderr)