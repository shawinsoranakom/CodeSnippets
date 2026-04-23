def _safe_extract_zip(zip_file, extract_to):
    """
    Safely extract a zip file, preventing zipslip attacks.

    Args:
        zip_file: ZipFile object to extract
        extract_to: Directory to extract to

    Raises:
        ValueError: If any archive entry contains unsafe paths
    """
    # Normalize the extraction directory path
    extract_to = Path(extract_to).resolve(strict=False)

    for member in zip_file.infolist():
        # Get the normalized path
        filename = os.path.normpath(member.filename)

        # Check for directory traversal attempts
        if filename.startswith(("/", "\\")):
            raise ValueError(f"Archive entry has absolute path: {member.filename}")

        if len(filename) >= 2 and filename[1] == ":" and filename[0].isalpha():
            raise ValueError(f"Archive entry has absolute path: {member.filename}")

        if ".." in re.split(_PATH_SEP_PATTERN, filename):
            raise ValueError(
                f"Archive entry contains directory traversal: {member.filename}"
            )

        # Construct the full extraction path and verify it's within extract_to
        out = (extract_to / filename).resolve(strict=False)

        if not out.is_relative_to(extract_to):
            raise ValueError(
                f"Archive entry escapes target directory: {member.filename}"
            )

        # Extract the member safely
        zip_file.extract(member, extract_to)