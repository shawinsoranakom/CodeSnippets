def result_to_middle_json(model_output_blocks_list, image_writer):
    middle_json = {"pdf_info": [], "_backend":"office", "_version_name": __version__}
    for index, page_blocks in enumerate(model_output_blocks_list):
        page_info = blocks_to_page_info(page_blocks, image_writer, index)
        middle_json["pdf_info"].append(page_info)

    section_counters: dict[int, int] = defaultdict(int)
    for page_info in middle_json["pdf_info"]:
        for block in page_info.get("para_blocks", []):
            if block.get("type") != BlockType.TITLE:
                continue
            level = block.get("level", 1)
            if block.get("is_numbered_style", False):
                # Ensure all ancestor levels start at 1 (never 0)
                for ancestor in range(1, level):
                    if section_counters[ancestor] == 0:
                        section_counters[ancestor] = 1
                # Increment current level counter and reset all deeper levels
                section_counters[level] += 1
                for deeper in list(section_counters.keys()):
                    if deeper > level:
                        section_counters[deeper] = 0
                # Build section number string, e.g. "1.2.1."
                section_number = ".".join(
                    str(section_counters[l]) for l in range(1, level + 1)
                ) + "."
                block["section_number"] = section_number
            else:
                # Some documents embed the section number directly in the content
                # (is_numbered_style=False).  Parse it and sync the counters so
                # that subsequent numbered blocks continue from the right base.
                lines = block.get("lines", [])
                content = ""
                if lines and lines[0].get("spans"):
                    content = lines[0]["spans"][0].get("content", "")
                parts = _extract_section_parts_from_content(content, level)
                if parts:
                    for k, v in enumerate(parts, start=1):
                        section_counters[k] = v
                    # Reset all deeper levels
                    for deeper in list(section_counters.keys()):
                        if deeper > level:
                            section_counters[deeper] = 0

    _link_index_entries_by_anchor(middle_json)
    return middle_json