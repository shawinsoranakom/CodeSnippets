def _dedup_rows(
        rows: list[list[str]],
    ) -> list[list[str]]:
        """Remove consecutive duplicate rows (same text ignoring bold)."""
        if not rows:
            return rows
        _bold_tag = re.compile(r"</?b>")
        result = [rows[0]]
        for row in rows[1:]:
            prev_text = [_bold_tag.sub("", c) for c in result[-1]]
            cur_text = [_bold_tag.sub("", c) for c in row]
            if cur_text != prev_text:
                result.append(row)
            else:
                prev_bold = sum(1 for c in result[-1] if "<b>" in c)
                cur_bold = sum(1 for c in row if "<b>" in c)
                if cur_bold > prev_bold:
                    result[-1] = row
        return result