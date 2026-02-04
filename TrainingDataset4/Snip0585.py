def check_docs_in_sync(output_dir: Path, blocks: list[BlockDoc]) -> bool:
    """
    Check if generated docs match existing docs.

    Returns True if in sync, False otherwise.
    """
    output_dir = Path(output_dir)
    file_mapping = get_block_file_mapping(blocks)

    all_match = True
    out_of_sync_details: list[tuple[str, list[str]]] = []

    for file_path, file_blocks in file_mapping.items():
        full_path = output_dir / file_path

        if not full_path.exists():
            block_names = [b.name for b in sorted(file_blocks, key=lambda b: b.name)]
            print(f"MISSING: {file_path}")
            print(f"  Blocks: {', '.join(block_names)}")
            out_of_sync_details.append((file_path, block_names))
            all_match = False
            continue

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

        # Generate expected file header
        file_header = f"# {file_title}\n"
        file_header += "<!-- MANUAL: file_description -->\n"
        file_header += f"{file_description}\n"
        file_header += "<!-- END MANUAL -->\n"

        # Extract manual content from existing file
        manual_sections_by_block = {}
        for block in file_blocks:
            block_pattern = rf"(?:^|\n)## {re.escape(block.name)}\s*\n(.*?)(?=\n---|\Z)"
            block_match = re.search(block_pattern, existing_content, re.DOTALL)
            if block_match:
                manual_sections_by_block[block.name] = extract_manual_content(
                    block_match.group(1)
                )

        # Generate expected content and check each block individually
        content_parts = []
        mismatched_blocks = []
        for block in sorted(file_blocks, key=lambda b: b.name):
            manual_content = manual_sections_by_block.get(block.name, {})
            expected_block_content = generate_block_markdown(
                block,
                manual_content,
            )
            content_parts.append(expected_block_content)

            # Check if this specific block's section exists and matches
            # Include the --- separator to match generate_block_markdown output
            block_pattern = rf"(?:^|\n)(## {re.escape(block.name)}\s*\n.*?\n---\n)"
            block_match = re.search(block_pattern, existing_content, re.DOTALL)
            if not block_match:
                mismatched_blocks.append(f"{block.name} (missing)")
            elif block_match.group(1).strip() != expected_block_content.strip():
                mismatched_blocks.append(block.name)

        # Add file-level additional_content to expected content (matches write_block_docs)
        file_additional = extract_manual_content(existing_content).get(
            "additional_content", ""
        )
        if file_additional:
            content_parts.append("<!-- MANUAL: additional_content -->")
            content_parts.append(file_additional)
            content_parts.append("<!-- END MANUAL -->")
            content_parts.append("")

        expected_content = file_header + "\n" + "\n".join(content_parts)

        if existing_content.strip() != expected_content.strip():
            print(f"OUT OF SYNC: {file_path}")
            if mismatched_blocks:
                print(f"  Affected blocks: {', '.join(mismatched_blocks)}")
            out_of_sync_details.append((file_path, mismatched_blocks))
            all_match = False

    # Check overview at the parent directory (docs/integrations/)
    root_dir = output_dir.parent
    block_dir_name = output_dir.name  # "block-integrations"
    block_dir_prefix = f"{block_dir_name}/"

    overview_path = root_dir / "README.md"
    if overview_path.exists():
        existing_overview = overview_path.read_text()
        expected_overview = generate_overview_table(blocks, block_dir_prefix)
        if existing_overview.strip() != expected_overview.strip():
            print("OUT OF SYNC: README.md (overview)")
            print("  The blocks overview table needs regeneration")
            out_of_sync_details.append(("README.md", ["overview table"]))
            all_match = False
    else:
        print("MISSING: README.md (overview)")
        out_of_sync_details.append(("README.md", ["overview table"]))
        all_match = False

    # Check SUMMARY.md at the parent directory
    summary_path = root_dir / "SUMMARY.md"
    if summary_path.exists():
        existing_summary = summary_path.read_text()
        expected_summary = generate_summary_md(blocks, root_dir, block_dir_prefix)
        if existing_summary.strip() != expected_summary.strip():
            print("OUT OF SYNC: SUMMARY.md (navigation)")
            print("  The GitBook navigation needs regeneration")
            out_of_sync_details.append(("SUMMARY.md", ["navigation"]))
            all_match = False
    else:
        print("MISSING: SUMMARY.md (navigation)")
        out_of_sync_details.append(("SUMMARY.md", ["navigation"]))
        all_match = False

    # Check for unfilled manual sections
    unfilled_patterns = [
        "_Add a description of this category of blocks._",
        "_Add technical explanation here._",
        "_Add practical use case examples here._",
    ]
    files_with_unfilled = []
    for file_path in file_mapping.keys():
        full_path = output_dir / file_path
        if full_path.exists():
            content = full_path.read_text()
            unfilled_count = sum(1 for p in unfilled_patterns if p in content)
            if unfilled_count > 0:
                files_with_unfilled.append((file_path, unfilled_count))

    if files_with_unfilled:
        print("\nWARNING: Files with unfilled manual sections:")
        for file_path, count in sorted(files_with_unfilled):
            print(f"  {file_path}: {count} unfilled section(s)")
        print(
            f"\nTotal: {len(files_with_unfilled)} files with unfilled manual sections"
        )

    return all_match
