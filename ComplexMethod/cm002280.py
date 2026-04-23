def _process_typed_dict_docstrings(
    candidate_file: str,
    overwrite: bool = False,
    tree: ast.Module | None = None,
) -> tuple[list[str], list[str], list[str]]:
    """
    Check and optionally fix TypedDict docstrings.
    Runs as a separate pass after @auto_docstring processing.

    Args:
        candidate_file: Path to the file to process
        overwrite: Whether to fix issues by writing to the file
        tree: Pre-parsed AST tree to avoid re-parsing the file

    Returns:
        Tuple of (missing_warnings, fill_warnings, redundant_warnings)
    """
    with open(candidate_file, "r", encoding="utf-8") as f:
        content = f.read()

    typed_dicts = _find_typed_dict_classes(content, tree=tree)
    if not typed_dicts:
        return [], [], []

    # Get source args for comparison
    source_args_doc = get_args_doc_from_source([ModelArgs, ImageProcessorArgs, ProcessorArgs])

    missing_warnings = []
    fill_warnings = []
    redundant_warnings = []

    # Process each TypedDict
    for td in typed_dicts:
        # Parse existing docstring
        documented_fields = {}
        remaining_docstring = ""
        if td["docstring"]:
            try:
                documented_fields, remaining_docstring = parse_docstring(td["docstring"])
            except Exception as e:
                logger.debug(f"Could not parse docstring for {td.get('name', 'unknown')}: {e}")

        # Find missing, fill, and redundant fields
        missing_fields = []
        fill_fields = []
        redundant_fields = []

        # Check fields that need custom documentation (not in source args)
        for field in td["fields"]:
            if field not in documented_fields:
                missing_fields.append(field)
            else:
                field_doc = documented_fields[field]
                desc = field_doc.get("description", "")
                type_str = field_doc.get("type", "")
                has_placeholder = "<fill_type>" in type_str or "<fill_docstring>" in desc
                if has_placeholder:
                    fill_fields.append(field)

        # Check ALL documented fields (including those in source args) for redundancy
        for field in documented_fields:
            if field in source_args_doc:
                field_doc = documented_fields[field]
                desc = field_doc.get("description", "")
                type_str = field_doc.get("type", "")
                has_placeholder = "<fill_type>" in type_str or "<fill_docstring>" in desc

                source_doc = source_args_doc[field]
                source_desc = source_doc.get("description", "").strip("\n ")
                field_desc = desc.strip("\n ")

                # Mark as redundant if has placeholder OR description matches source
                if has_placeholder or source_desc == field_desc:
                    redundant_fields.append(field)

        if missing_fields:
            field_list = ", ".join(sorted(missing_fields))
            missing_warnings.append(f"    - {td['name']} (line {td['line']}): undocumented fields: {field_list}")

        if fill_fields:
            field_list = ", ".join(sorted(fill_fields))
            fill_warnings.append(f"    - {td['name']} (line {td['line']}): fields with placeholders: {field_list}")

        if redundant_fields:
            field_list = ", ".join(sorted(redundant_fields))
            redundant_warnings.append(
                f"    - {td['name']} (line {td['line']}): redundant fields (in source): {field_list}"
            )

    # If overwrite mode, fix missing fields and remove redundant ones
    if overwrite and (missing_warnings or redundant_warnings):
        lines = content.split("\n")

        # Process TypedDicts in reverse order to avoid line number shifts
        for td in sorted(typed_dicts, key=lambda x: x["line"], reverse=True):
            # Parse existing docstring
            documented_fields = {}
            remaining_docstring = ""
            if td["docstring"]:
                try:
                    documented_fields, remaining_docstring = parse_docstring(td["docstring"])
                except Exception as e:
                    logger.debug(f"Could not parse docstring for {td.get('name', 'unknown')}: {e}")

            # Determine which fields to remove (redundant with source)
            fields_to_remove = set()
            for field in documented_fields:
                if field in source_args_doc:
                    field_doc = documented_fields[field]
                    desc = field_doc.get("description", "")
                    type_str = field_doc.get("type", "")
                    has_placeholder = "<fill_type>" in type_str or "<fill_docstring>" in desc

                    source_doc = source_args_doc[field]
                    source_desc = source_doc.get("description", "").strip("\n ")
                    field_desc = desc.strip("\n ")

                    # Remove if has placeholder OR description matches source
                    if has_placeholder or source_desc == field_desc:
                        fields_to_remove.add(field)

            # Check if any fields are missing or need removal
            has_missing = any(f not in documented_fields for f in td["fields"])
            has_changes = has_missing or len(fields_to_remove) > 0

            if not has_changes:
                continue

            # Build new docstring dict (preserving existing, removing redundant, adding missing)
            # We iterate over documented_fields first to preserve order, then add missing fields
            new_doc_dict = OrderedDict()

            # First, add documented fields that should be kept (not redundant)
            for field in documented_fields:
                if field not in fields_to_remove:
                    # Only keep fields that are either:
                    # 1. In td["fields"] (needs custom documentation)
                    # 2. Not in source_args_doc (might be inherited or custom)
                    if field in td["fields"] or field not in source_args_doc:
                        new_doc_dict[field] = documented_fields[field]

            # Then, add missing fields from td["fields"]
            for field in td["fields"]:
                if field not in documented_fields and field not in new_doc_dict:
                    # Add placeholder for missing field
                    new_doc_dict[field] = {
                        "type": "`<fill_type>`",
                        "optional": False,
                        "shape": None,
                        "description": "\n    <fill_docstring>",
                        "default": None,
                        "additional_info": None,
                    }

            # Build new docstring text
            class_line_idx = td["line"] - 1
            class_line = lines[class_line_idx]
            indent = len(class_line) - len(class_line.lstrip())

            # If all fields were removed, remove the docstring entirely
            if not new_doc_dict and not remaining_docstring:
                if td["docstring"] is not None:
                    doc_start_idx = td["docstring_start_line"] - 1
                    doc_end_idx = td["docstring_end_line"]
                    lines = lines[:doc_start_idx] + lines[doc_end_idx:]
                continue

            # Build docstring content (without indentation first)
            docstring_content = '"""\n'
            for field_name, field_doc in new_doc_dict.items():
                additional_info = field_doc.get("additional_info", "") or ""
                description = field_doc["description"]
                if description.endswith('"""'):
                    description = "\n".join(description.split("\n")[:-1])
                docstring_content += f"{field_name} ({field_doc['type']}{additional_info}):{description}\n"

            # Add remaining docstring content if any
            close_docstring = True
            if remaining_docstring:
                if remaining_docstring.endswith('"""'):
                    close_docstring = False
                end_str = "\n" if close_docstring else ""
                docstring_content += f"{set_min_indent(remaining_docstring, 0)}{end_str}"
            if close_docstring:
                docstring_content += '"""'

            # Apply proper indentation
            docstring_content = set_min_indent(docstring_content, indent + 4)
            docstring_lines = docstring_content.split("\n")

            # Replace in lines
            if td["docstring"] is None:
                # Insert new docstring after class definition
                insert_idx = class_line_idx + 1
                lines = lines[:insert_idx] + docstring_lines + lines[insert_idx:]
            else:
                # Replace existing docstring
                doc_start_idx = td["docstring_start_line"] - 1
                doc_end_idx = td["docstring_end_line"]  # end_lineno is 1-based, we want to include this line
                lines = lines[:doc_start_idx] + docstring_lines + lines[doc_end_idx:]

        # Write updated content
        with open(candidate_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    return missing_warnings, fill_warnings, redundant_warnings