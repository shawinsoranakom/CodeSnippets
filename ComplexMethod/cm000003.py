def lint_file(path, cfg):
    """
    Analyzes a single Markdown file for RTL/LTR issues.

    Args:
        path (str): The path to the Markdown file to analyze.
        cfg (dict): The configuration dictionary.

    Returns:
        list: A list of strings, where each string represents a detected issue,
              formatted for GitHub Actions output.
    """
    # Initialize the list of issues
    issues = []

    # Try to read the file content and handle potential errors
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except Exception as e:
        return [f"::error file={path},line=1::Cannot read file: {e}"] # Return as a list of issues

    # Extract configuration parameters for easier access and readability
    keywords_orig = cfg['ltr_keywords']
    symbols = cfg['ltr_symbols']
    pure_ltr_re = re.compile(cfg['pure_ltr_pattern'])
    rtl_char_re = re.compile(cfg['rtl_chars_pattern'])
    sev = cfg['severity']
    ignore_meta = set(cfg['ignore_meta'])
    min_len = cfg['min_ltr_length']

    # chr(0x200F) = RLM Unicode character
    # chr(0x200E) = LRM Unicode character
    # These control character must be added here in the code and not in the YAML configuration file,
    # due to the fact that if we included them in the YAML file they would be invisible and, therefore,
    # the YAML file would be less readable
    RLM = [chr(0x200F)] + cfg['rlm_entities']
    LRM = [chr(0x200E)] + cfg['lrm_entities']

    # Determine the directionality context of the file (RTL or LTR) based on the filename
    file_direction_ctx = 'rtl' if is_rtl_filename(path) else 'ltr'

    # Stack to manage block-level direction contexts for nested divs.
    # Initialized with the file's base direction context.
    block_context_stack = [file_direction_ctx]

    # Iterate over each line of the file with its line number
    for idx, line in enumerate(lines, 1):

        # The active block direction context for the current line is the top of the stack.
        active_block_direction_ctx = block_context_stack[-1]

        # Skip lines that start a code block (```)
        if CODE_FENCE_START.match(line): continue

        # Find all opening and closing <div> tags on the line to handle cases
        # where there can be multiple <div> opening and closing on the same line
        div_tags = re.findall(r"(<div[^>]*dir=['\"](rtl|ltr)['\"][^>]*>|</div>)", line, re.IGNORECASE)

        # Process each found tag in order to correctly update the context stack
        for tag_tuple in div_tags:
            # re.findall with multiple capture groups returns a list of tuples:
            # tag: The full matched tag (e.g., '<div...>' or '</div>')
            # direction: The captured direction ('rtl' or 'ltr'), or empty for a closing tag
            tag, direction = tag_tuple

            # If it's an opening tag with 'markdown="1"', push the new context
            if tag.startswith('<div') and 'markdown="1"' in tag:
                block_context_stack.append(direction.lower())
            # If it's a closing tag and we are inside a div, pop the context
            elif tag == '</div>' and len(block_context_stack) > 1:
                block_context_stack.pop()
        # Check if the line is a Markdown list item
        list_item = LIST_ITEM_RE.match(line)

        # If the line is not a list item, skip to the next line
        if not list_item: continue

        # Extract the text content of the list item and remove leading/trailing whitespace
        text = list_item.group(1).strip()

        # Extract item parts (title, author, metadata) if it matches the book format
        book_item = BOOK_ITEM_RE.match(text)

        # If the current line is a book item
        if book_item:

            # Extract title, author, and metadata from the book item
            title = book_item.group('title')
            author = (book_item.group('author') or '').strip()
            meta = (book_item.group('meta') or '').strip()

            # If the list item is just a link like the link in the section "### Index" of the .md files (i.e., [Title](url))
            is_link_only_item = not author and not meta

        # Otherwise, if it's not a book item
        else:

            # Initialize title, author, and meta with empty strings
            title, author, meta = text, '', ''

            # Set is_link_only_item to False
            is_link_only_item = False

        # Specific check: RTL author followed by LTR metadata (e.g., اسم المؤلف (PDF))
        if  active_block_direction_ctx == 'rtl' and \
            author and meta and \
            rtl_char_re.search(author) and pure_ltr_re.match(meta) and \
            len(meta) >= min_len and \
            not any(author.strip().endswith(rlm_marker) for rlm_marker in RLM):
            issues.append(
                f"::{sev['author_meta'].lower()} file={path},line={idx}::RTL author '{author.strip()}' followed by LTR meta '{meta}' may need '&rlm;' after author."
            )

        # Analyze individual parts of the item (title, author, metadata)
        for part, raw_text in [('title', title), ('author', author), ('meta', meta)]:

            # Skip if the part is empty or if it's metadata to be ignored (e.g., "PDF")
            if not raw_text or (part=='meta' and raw_text in ignore_meta): continue

            # Split the part into segments based on <span> tags with dir attributes
            segments = split_by_span(raw_text, active_block_direction_ctx)

            # Filter keywords to avoid duplicates with symbols (a symbol can contain a keyword)
            filtered_keywords = [kw for kw in keywords_orig]
            for sym in symbols:
                filtered_keywords = [kw for kw in filtered_keywords if kw not in sym]

            # Iterate over each text segment and its directionality context
            for segment_text, segment_direction_ctx in segments:

                # Remove leading/trailing whitespace from the segment text
                s = segment_text.strip()

                # In the following block of code, it's checked if the segment is entirely enclosed in parentheses or brackets.
                # In fact, if the content inside is purely LTR or RTL, its display is usually
                # well-isolated by the parentheses or brackets and less prone to BIDI issues.
                # Mixed LTR/RTL content inside brackets should still be checked.

                # Check if the segment is entirely enclosed in parentheses or brackets.
                m_bracket = BRACKET_CONTENT_RE.fullmatch(s)
                if m_bracket:

                    # If it is, extract the content inside the parentheses/brackets.
                    inner_content = m_bracket.group(2)

                    # Determine if the inner content is purely LTR or purely RTL.
                    is_pure_ltr_inner = pure_ltr_re.match(inner_content) is not None

                    # Check for pure RTL: contains RTL chars AND no LTR chars (using [A-Za-z0-9] as a proxy for common LTR chars)
                    is_pure_rtl_inner = rtl_char_re.search(inner_content) is not None and re.search(r"[A-Za-z0-9]", inner_content) is None

                    # Skip the segment ONLY if the content inside is purely LTR or purely RTL.
                    if is_pure_ltr_inner or is_pure_rtl_inner: continue

                # Skip if it's inline code (i.e., `...`) or already contains directionality markers (e.g., &rlm; or &lrm;)
                if any([
                    INLINE_CODE_RE.match(s),
                    any(mk in s for mk in RLM+LRM)
                ]):
                    continue

                # Check for BIDI mismatch: if the text contains both RTL and LTR
                # characters and the calculated visual order differs from the logical order.
                if rtl_char_re.search(s) and re.search(r"[A-Za-z0-9]", s):
                    disp = get_display(s)
                    if disp != s:
                        issues.append(
                            f"::{sev['bidi_mismatch'].lower()} file={path},line={idx}::BIDI mismatch in {part}: the text '{s}' is displayed as '{disp}'"
                        )

                # If the segment context is LTR, there is no need to check LTR keywords and LTR symbols
                # that might need directionality markers, so we can skip the next checks and move on to the next line of the file
                if segment_direction_ctx != 'rtl': continue

                # Skip keyword and symbol checks for titles of link-only items (e.g., in the Index section of markdown files)
                if not (part == 'title' and is_link_only_item):

                    # Check for LTR symbols: if an LTR symbol is present and lacks an '&lrm;' marker
                    for sym in symbols:
                        if sym in s and not any(m in s for m in LRM):
                            issues.append(
                                f"::{sev['symbol'].lower()} file={path},line={idx}::Symbol '{sym}' in {part} '{s}' may need trailing '&lrm;' marker."
                            )

                    # Check for LTR keywords: if an LTR keyword is present and lacks an RLM marker
                    for kw in filtered_keywords:
                        if kw in s and not any(m in s for m in RLM):
                            issues.append(
                                f"::{sev['keyword'].lower()} file={path},line={idx}::Keyword '{kw}' in {part} '{s}' may need trailing '&rlm;' marker."
                            )

                # Check for "Pure LTR" text: if the segment is entirely LTR,
                # it's not a title, and has a minimum length, it might need a trailing RLM.
                if (part != 'title') and pure_ltr_re.match(s) and not rtl_char_re.search(s) and len(s)>=min_len:
                    issues.append(
                        f"::{sev['pure_ltr'].lower()} file={path},line={idx}::Pure LTR text '{s}' in {part} of RTL context may need trailing '&rlm;' marker."
                    )

    # Check for unclosed div tags at the end of the file
    if len(block_context_stack) > 1:
        issues.append(
            f"::error file={path},line={len(lines)}::Found unclosed <div dir='...'> tag. "
            f"The final block context is '{block_context_stack[-1]}', not the file's base '{file_direction_ctx}'."
        )

    # Return the list of found issues
    return issues