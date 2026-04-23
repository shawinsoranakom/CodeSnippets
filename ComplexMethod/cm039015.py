def check_spdx_header_status(file_path):
    """Check SPDX header status of the file"""
    with open(file_path, encoding="UTF-8") as file:
        lines = file.readlines()
        if not lines:
            # Empty file
            return SPDXStatus.EMPTY

        # Skip shebang line
        start_idx = 0
        if lines and lines[0].startswith("#!"):
            start_idx = 1

        has_license = False
        has_copyright = False

        # Check all lines for SPDX headers (not just the first two)
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if line == LICENSE_LINE:
                has_license = True
            elif line == COPYRIGHT_LINE:
                has_copyright = True

        # Determine status based on what we found
        if has_license and has_copyright:
            return SPDXStatus.COMPLETE
        elif has_license and not has_copyright:
            # Only has license line
            return SPDXStatus.MISSING_COPYRIGHT
            # Only has copyright line
        elif not has_license and has_copyright:
            return SPDXStatus.MISSING_LICENSE
        else:
            # Completely missing both lines
            return SPDXStatus.MISSING_BOTH