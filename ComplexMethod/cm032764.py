def resolve_outline_levels(self, line_records):
        outlines = self.extract_outlines()
        if not line_records or len(outlines) / len(line_records) <= 0.03:
            return None

        max_level = max(level for _, level, _ in outlines) + 1
        levels = []
        for record in line_records:
            if record["doc_type_kwd"] != "text":
                levels.append(BODY_LEVEL)
                continue
            text = record["text"]
            for outline_text, level, _ in outlines:
                if self._outline_similarity(outline_text, text) > 0.8:
                    levels.append(level + 1)
                    break
            else:
                levels.append(BODY_LEVEL)

        return {
            "levels": levels,
            "most_level": max(1, max_level - 1),
            "source": "outline",
        }