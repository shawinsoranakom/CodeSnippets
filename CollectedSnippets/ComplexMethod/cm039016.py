def add_header(file_path, status):
    """Add or supplement SPDX header based on status"""
    with open(file_path, "r+", encoding="UTF-8") as file:
        lines = file.readlines()
        file.seek(0, 0)
        file.truncate()

        if status == SPDXStatus.MISSING_BOTH:
            # Completely missing, add complete header
            if lines and lines[0].startswith("#!"):
                # Preserve shebang line
                file.write(lines[0])
                file.write(FULL_SPDX_HEADER + "\n")
                file.writelines(lines[1:])
            else:
                # Add header directly
                file.write(FULL_SPDX_HEADER + "\n")
                file.writelines(lines)

        elif status == SPDXStatus.MISSING_COPYRIGHT:
            # Only has license line, need to add copyright line
            # Find the license line and add copyright line after it
            for i, line in enumerate(lines):
                if line.strip() == LICENSE_LINE:
                    # Insert copyright line after license line
                    lines.insert(
                        i + 1,
                        f"{COPYRIGHT_LINE}\n",
                    )
                    break

            file.writelines(lines)

        elif status == SPDXStatus.MISSING_LICENSE:
            # Only has copyright line, need to add license line
            # Find the copyright line and add license line before it
            for i, line in enumerate(lines):
                if line.strip() == COPYRIGHT_LINE:
                    # Insert license line before copyright line
                    lines.insert(i, f"{LICENSE_LINE}\n")
                    break
            file.writelines(lines)