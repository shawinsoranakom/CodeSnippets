def extract_warnings_from_single_artifact(artifact_path, targets):
    """Extract warnings from a downloaded artifact (in .zip format)"""
    selected_warnings = set()
    buffer = []

    def parse_line(fp):
        for line in fp:
            if isinstance(line, bytes):
                line = line.decode("UTF-8")
            if "warnings summary (final)" in line:
                continue
            # This means we are outside the body of a warning
            elif not line.startswith(" "):
                # process a single warning and move it to `selected_warnings`.
                if len(buffer) > 0:
                    warning = "\n".join(buffer)
                    # Only keep the warnings specified in `targets`
                    if any(f": {x}: " in warning for x in targets):
                        selected_warnings.add(warning)
                    buffer.clear()
                continue
            else:
                line = line.strip()
                buffer.append(line)

    if from_gh:
        for filename in os.listdir(artifact_path):
            file_path = os.path.join(artifact_path, filename)
            if not os.path.isdir(file_path):
                # read the file
                if filename != "warnings.txt":
                    continue
                with open(file_path) as fp:
                    parse_line(fp)
    else:
        try:
            with zipfile.ZipFile(artifact_path) as z:
                for filename in z.namelist():
                    if not os.path.isdir(filename):
                        # read the file
                        if filename != "warnings.txt":
                            continue
                        with z.open(filename) as fp:
                            parse_line(fp)
        except Exception:
            logger.warning(
                f"{artifact_path} is either an invalid zip file or something else wrong. This file is skipped."
            )

    return selected_warnings