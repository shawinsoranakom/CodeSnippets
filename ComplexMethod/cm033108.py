def _is_garbled_text(text, threshold=0.5):
        """Check if a text string contains too many garbled characters.

        Examines each character and determines if the overall proportion
        of garbled characters exceeds the given threshold. Also detects
        pdfminer's CID placeholder patterns like '(cid:123)'.
        """
        if not text or not text.strip():
            return False
        if RAGFlowPdfParser._CID_PATTERN.search(text):
            return True
        garbled_count = 0
        total = 0
        for ch in text:
            if ch.isspace():
                continue
            total += 1
            if RAGFlowPdfParser._is_garbled_char(ch):
                garbled_count += 1
        if total == 0:
            return False
        return garbled_count / total >= threshold