def _is_garbled_by_font_encoding(page_chars, min_chars=20):
        """Detect garbled text caused by broken font encoding mappings.

        Some PDFs (especially older Chinese standards) embed custom fonts that
        map CJK glyphs to ASCII codepoints. The extracted text appears as
        random ASCII punctuation/symbols instead of actual CJK characters.

        Detection strategy: if a significant proportion of characters come from
        subset-embedded fonts and the page produces overwhelmingly ASCII
        (punctuation, digits, symbols) with virtually no CJK/Hangul/Kana
        characters, the page is likely garbled due to broken font encoding.
        """
        if not page_chars or len(page_chars) < min_chars:
            return False

        subset_font_count = 0
        total_non_space = 0
        ascii_punct_sym = 0
        cjk_like = 0

        for c in page_chars:
            text = c.get("text", "")
            fontname = c.get("fontname", "")
            if not text or text.isspace():
                continue
            total_non_space += 1

            if RAGFlowPdfParser._has_subset_font_prefix(fontname):
                subset_font_count += 1

            cp = ord(text[0])
            if (0x2E80 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
                    or 0x20000 <= cp <= 0x2FA1F
                    or 0xAC00 <= cp <= 0xD7AF
                    or 0x3040 <= cp <= 0x30FF):
                cjk_like += 1
            elif (0x21 <= cp <= 0x2F or 0x3A <= cp <= 0x40
                    or 0x5B <= cp <= 0x60 or 0x7B <= cp <= 0x7E):
                ascii_punct_sym += 1

        if total_non_space < min_chars:
            return False

        subset_ratio = subset_font_count / total_non_space
        if subset_ratio < 0.3:
            return False

        cjk_ratio = cjk_like / total_non_space
        punct_ratio = ascii_punct_sym / total_non_space
        if cjk_ratio < 0.05 and punct_ratio > 0.4:
            return True

        return False