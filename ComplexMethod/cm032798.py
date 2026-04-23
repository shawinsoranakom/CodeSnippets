def _extract_metadata_text(binary: bytes) -> list[dict]:
    """
    Extract text blocks from PDF metadata (with coordinate info)

    Strategy:
    1. Use whitelist strategy to filter decorative layer noise chars (embedded font or structure tag = body text)
    2. Safe fallback: if filtered chars are less than 30% of original, skip filtering to avoid false positives
    3. Use extract_words for word-level extraction (with real coordinates)
    4. Aggregate adjacent words into line-level text blocks by Y coordinate
    5. Additionally extract table content (many resumes use table layouts)

    Args:
        binary: PDF file binary content
    Returns:
        List of text blocks, each containing text, x0, top, x1, bottom, page fields
    """
    try:
        import pdfplumber
        blocks = []
        with pdfplumber.open(BytesIO(binary)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_width = page.width or 600

                # Filter decorative layer noise chars (whitelist strategy based on embedded font + structure tag)
                # Safe fallback: if filtered chars are less than 30% of original, the PDF's body text
                # may use non-embedded fonts without structure tags, skip filtering to avoid false positives
                try:
                    original_char_count = len(page.chars)
                    filtered_page = page.filter(
                        lambda obj: not _is_noise_char(obj)
                    )
                    filtered_char_count = len(filtered_page.chars)
                    if original_char_count > 0 and filtered_char_count < original_char_count * 0.3:
                        # Filtered out over 70% of chars, likely false positives, fall back to original page
                        filtered_page = page
                except Exception:
                    filtered_page = page

                # Use extract_words for extraction (with real coordinates)
                words = []
                try:
                    words = filtered_page.extract_words(
                        keep_blank_chars=False, use_text_flow=True
                    )
                except Exception:
                    pass

                if words:
                    # Aggregate adjacent words into line-level text blocks by Y coordinate
                    # Words on the same line: top coordinate difference within threshold
                    line_threshold = 5  # Y coordinate difference threshold (unit: PDF points)
                    current_line_words = [words[0]]

                    def _flush_line(line_words):
                        """Merge words in a line into a single text block"""
                        # Sort by x0 to ensure left-to-right order
                        line_words.sort(key=lambda w: float(w.get("x0", 0)))
                        texts = []
                        for w in line_words:
                            texts.append(w.get("text", ""))
                        merged_text = " ".join(texts)
                        if not merged_text.strip():
                            return None
                        return {
                            "text": merged_text.strip(),
                            "x0": float(min(w.get("x0", 0) for w in line_words)),
                            "top": float(min(w.get("top", 0) for w in line_words)),
                            "x1": float(max(w.get("x1", 0) for w in line_words)),
                            "bottom": float(max(w.get("bottom", 0) for w in line_words)),
                            "page": page_idx,
                        }

                    for w in words[1:]:
                        w_top = float(w.get("top", 0))
                        cur_top = float(current_line_words[0].get("top", 0))
                        if abs(w_top - cur_top) <= line_threshold:
                            current_line_words.append(w)
                        else:
                            block = _flush_line(current_line_words)
                            if block:
                                blocks.append(block)
                            current_line_words = [w]

                    # Process the last line
                    if current_line_words:
                        block = _flush_line(current_line_words)
                        if block:
                            blocks.append(block)
                else:
                    # Fall back to extract_text when extract_words fails
                    page_text = None
                    try:
                        page_text = page.extract_text()
                    except Exception:
                        pass
                    if page_text and page_text.strip():
                        raw_lines = page_text.split("\n")
                        line_height = 16
                        for i, line in enumerate(raw_lines):
                            cleaned = line.strip()
                            if not cleaned:
                                continue
                            blocks.append({
                                "text": cleaned,
                                "x0": 0,
                                "top": i * line_height,
                                "x1": page_width,
                                "bottom": i * line_height + line_height - 2,
                                "page": page_idx,
                            })

                # Extract table content from the page
                # Many resumes use table layouts (e.g., personal info section), extract_words may miss table structure
                try:
                    tables = page.extract_tables()
                    if tables:
                        page_blocks = [b for b in blocks if b["page"] == page_idx]
                        max_top = max((b["top"] for b in page_blocks), default=0) + 20
                        row_height = 16

                        for table in tables:
                            for row in table:
                                if not row:
                                    continue
                                cells = [str(c).strip() for c in row if c and str(c).strip()]
                                if not cells:
                                    continue
                                row_text = " | ".join(cells)
                                # Dedup: check if table content was already extracted by extract_words
                                is_dup = False
                                for pb in page_blocks:
                                    if all(c in pb["text"] for c in cells[:2]):
                                        is_dup = True
                                        break
                                if is_dup:
                                    continue
                                blocks.append({
                                    "text": row_text,
                                    "x0": 0,
                                    "top": max_top,
                                    "x1": page_width,
                                    "bottom": max_top + row_height - 2,
                                    "page": page_idx,
                                })
                                max_top += row_height
                except Exception as e:
                    logger.debug(f"PDF table extraction skipped (page {page_idx}): {e}")
        return blocks
    except Exception as e:
        logger.warning(f"PDF metadata extraction failed: {e}")
        return []