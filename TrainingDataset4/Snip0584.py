def write_block_docs(
    output_dir: Path,
    blocks: list[BlockDoc],
    verbose: bool = False,
) -> dict[str, str]:
    """
    Write block documentation files.

    Returns dict of {file_path: content} for all generated files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_mapping = get_block_file_mapping(blocks)
    generated_files = {}

    for file_path, file_blocks in file_mapping.items():
        full_path = output_dir / file_path

        # Create subdirectories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing content for manual section preservation
        existing_content = ""
        if full_path.exists():
            existing_content = full_path.read_text()

        # Always generate title from file path (with fixes applied)
        file_title = file_path_to_title(file_path)

        # Extract existing file description if present (preserve manual content)
        file_header_pattern = (
            r"^# .+?\n<!-- MANUAL: file_description -->\n(.*?)\n<!-- END MANUAL -->"
        )
        file_header_match = re.search(file_header_pattern, existing_content, re.DOTALL)

        if file_header_match:
            file_description = file_header_match.group(1)
        else:
            file_description = "_Add a description of this category of blocks._"

        # Generate file header
        file_header = f"# {file_title}\n"
        file_header += "<!-- MANUAL: file_description -->\n"
        file_header += f"{file_description}\n"
        file_header += "<!-- END MANUAL -->\n"

        # Generate content for each block
        content_parts = []
        for block in sorted(file_blocks, key=lambda b: b.name):
            # Extract manual content specific to this block
            # Match block heading (h2) and capture until --- separator
            block_pattern = rf"(?:^|\n)## {re.escape(block.name)}\s*\n(.*?)(?=\n---|\Z)"
            block_match = re.search(block_pattern, existing_content, re.DOTALL)
            if block_match:
                manual_content = extract_manual_content(block_match.group(1))
            else:
                manual_content = {}

            content_parts.append(
                generate_block_markdown(
                    block,
                    manual_content,
                )
            )

        # Add file-level additional_content section if present
        file_additional = extract_manual_content(existing_content).get(
            "additional_content", ""
        )
        if file_additional:
            content_parts.append("<!-- MANUAL: additional_content -->")
            content_parts.append(file_additional)
            content_parts.append("<!-- END MANUAL -->")
            content_parts.append("")

        full_content = file_header + "\n" + "\n".join(content_parts)
        generated_files[str(file_path)] = full_content

        if verbose:
            print(f"  Writing {file_path} ({len(file_blocks)} blocks)")

        full_path.write_text(full_content)

    # Generate overview file at the parent directory (docs/integrations/)
    # with links prefixed to point into block-integrations/
    root_dir = output_dir.parent
    block_dir_name = output_dir.name  # "block-integrations"
    block_dir_prefix = f"{block_dir_name}/"

    overview_content = generate_overview_table(blocks, block_dir_prefix)
    overview_path = root_dir / "README.md"
    generated_files["README.md"] = overview_content
    overview_path.write_text(overview_content)

    if verbose:
        print("  Writing README.md (overview) to parent directory")

    # Generate SUMMARY.md for GitBook navigation at the parent directory
    summary_content = generate_summary_md(blocks, root_dir, block_dir_prefix)
    summary_path = root_dir / "SUMMARY.md"
    generated_files["SUMMARY.md"] = summary_content
    summary_path.write_text(summary_content)

    if verbose:
        print("  Writing SUMMARY.md (navigation) to parent directory")

    return generated_files
