def verify_local_file_with_checksum_url(file_path: str, checksum_url: str, filename=None) -> bool:
    """
    Verify a local file against checksums from an online checksum file.

    :param file_path: Path to the local file to verify
    :param checksum_url: URL of the checksum file
    :param filename: Filename to look for in checksum file (defaults to basename of file_path)
    :return: True if verification succeeds, False otherwise

    note: The algorithm is automatically detected based on checksum length:

       * 32 characters: MD5
       * 40 characters: SHA1
       * 64 characters: SHA256
       * 128 characters: SHA512
    """
    # Get checksums from URL
    LOG.debug("Fetching checksums from %s...", checksum_url)
    checksums = parse_checksum_file_from_url(checksum_url)

    if not checksums:
        raise ChecksumException(f"No checksums found in {checksum_url}")

    # Determine filename to look for
    if filename is None:
        filename = os.path.basename(file_path)

    # Find checksum for our file
    if filename not in checksums:
        # Try with different path variations
        possible_names = [
            filename,
            os.path.basename(filename),  # just filename without path
            filename.replace("\\", "/"),  # Unix-style paths
            filename.replace("/", "\\"),  # Windows-style paths
        ]

        found = False
        for name in possible_names:
            if name in checksums:
                filename = name
                found = True
                break

        if not found:
            raise ChecksumException(f"Checksum for {filename} not found in {checksum_url}")

    expected_checksum = checksums[filename]

    # Detect algorithm based on checksum length
    checksum_length = len(expected_checksum)
    if checksum_length == 32:
        algorithm = "md5"
    elif checksum_length == 40:
        algorithm = "sha1"
    elif checksum_length == 64:
        algorithm = "sha256"
    elif checksum_length == 128:
        algorithm = "sha512"
    else:
        raise ChecksumException(f"Unsupported checksum length: {checksum_length}")

    # Calculate checksum of local file
    LOG.debug("Calculating %s checksum of %s...", algorithm, file_path)
    calculated_checksum = calculate_file_checksum(file_path, algorithm)

    is_valid = calculated_checksum == expected_checksum.lower()

    if not is_valid:
        LOG.error(
            "Checksum mismatch for %s: calculated %s, expected %s",
            file_path,
            calculated_checksum,
            expected_checksum,
        )
        raise ChecksumException(
            f"Checksum mismatch for {file_path}: calculated {calculated_checksum}, expected {expected_checksum}"
        )
    LOG.debug("Checksum verification successful for %s", file_path)

    # Compare checksums
    return calculated_checksum == expected_checksum.lower()