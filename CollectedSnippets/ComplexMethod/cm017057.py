def extract_multiline_code_blocks(text: list[str]) -> list[MultilineCodeBlockInfo]:
    blocks: list[MultilineCodeBlockInfo] = []

    in_code_block3 = False
    in_code_block4 = False
    current_block_lang = ""
    current_block_start_line = -1
    current_block_lines = []

    for line_no, line in enumerate(text, start=1):
        stripped = line.lstrip()

        # --- Detect opening fence ---
        if not (in_code_block3 or in_code_block4):
            if stripped.startswith("```"):
                current_block_start_line = line_no
                count = len(stripped) - len(stripped.lstrip("`"))
                if count == 3:
                    in_code_block3 = True
                    current_block_lang = get_code_block_lang(stripped)
                    current_block_lines = [line]
                    continue
                elif count >= 4:
                    in_code_block4 = True
                    current_block_lang = get_code_block_lang(stripped)
                    current_block_lines = [line]
                    continue

        # --- Detect closing fence ---
        elif in_code_block3:
            if stripped.startswith("```"):
                count = len(stripped) - len(stripped.lstrip("`"))
                if count == 3:
                    current_block_lines.append(line)
                    blocks.append(
                        MultilineCodeBlockInfo(
                            lang=current_block_lang,
                            start_line_no=current_block_start_line,
                            content=current_block_lines,
                        )
                    )
                    in_code_block3 = False
                    current_block_lang = ""
                    current_block_start_line = -1
                    current_block_lines = []
                    continue
            current_block_lines.append(line)

        elif in_code_block4:
            if stripped.startswith("````"):
                count = len(stripped) - len(stripped.lstrip("`"))
                if count >= 4:
                    current_block_lines.append(line)
                    blocks.append(
                        MultilineCodeBlockInfo(
                            lang=current_block_lang,
                            start_line_no=current_block_start_line,
                            content=current_block_lines,
                        )
                    )
                    in_code_block4 = False
                    current_block_lang = ""
                    current_block_start_line = -1
                    current_block_lines = []
                    continue
            current_block_lines.append(line)

    return blocks