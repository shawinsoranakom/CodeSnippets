def update_mkdocs_file(reference_yaml: str) -> None:
    """Update the mkdocs.yaml file with the new reference section only if changes in document paths are detected."""
    mkdocs_content = MKDOCS_YAML.read_text()

    # Find the top-level Reference section
    ref_pattern = r"(\n  - Reference:[\s\S]*?)(?=\n  - \w|$)"
    ref_match = re.search(ref_pattern, mkdocs_content)

    # Build new section with proper indentation
    new_section_lines = ["\n  - Reference:"]
    new_section_lines.extend(
        f"    {line}"
        for line in reference_yaml.splitlines()
        if line.strip() != "- reference:"  # Skip redundant header
    )
    new_ref_section = "\n".join(new_section_lines) + "\n"

    if ref_match:
        # We found an existing Reference section
        ref_section = ref_match.group(1)
        LOGGER.info(f"Found existing top-level Reference section ({len(ref_section)} chars)")

        # Compare only document paths
        existing_paths = extract_document_paths(ref_section)
        new_paths = extract_document_paths(new_ref_section)

        # Check if the document paths are the same (ignoring structure or formatting differences)
        if len(existing_paths) == len(new_paths) and set(existing_paths) == set(new_paths):
            LOGGER.info(f"No changes detected in document paths ({len(existing_paths)} items). Skipping update.")
            return

        LOGGER.info(f"Changes detected: {len(new_paths)} document paths vs {len(existing_paths)} existing")

        # Update content
        new_content = mkdocs_content.replace(ref_section, new_ref_section)
        MKDOCS_YAML.write_text(new_content)
        try:
            result = subprocess.run(
                ["npx", "prettier", "--write", str(MKDOCS_YAML)], capture_output=True, text=True, cwd=PACKAGE_DIR.parent
            )
            if result.returncode != 0:
                LOGGER.warning(f"prettier formatting failed: {result.stderr.strip()}")
        except FileNotFoundError:
            LOGGER.warning("prettier not found (install Node.js or run 'npm i -g prettier'), skipping YAML formatting")
        LOGGER.info(f"Updated Reference section in {MKDOCS_YAML}")
    elif help_match := re.search(r"(\n  - Help:)", mkdocs_content):
        # No existing Reference section, we need to add it
        help_section = help_match.group(1)
        # Insert before Help section
        new_content = mkdocs_content.replace(help_section, f"{new_ref_section}{help_section}")
        MKDOCS_YAML.write_text(new_content)
        LOGGER.info(f"Added new Reference section before Help in {MKDOCS_YAML}")
    else:
        LOGGER.warning("Could not find a suitable location to add Reference section")