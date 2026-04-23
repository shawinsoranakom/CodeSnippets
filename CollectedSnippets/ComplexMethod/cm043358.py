def is_data_table(self, table: etree.Element, **kwargs) -> bool:
        """
        Determine if a table is a data table (vs. layout table) using a scoring system.

        Args:
            table: The table element to evaluate
            **kwargs: Additional parameters (e.g., table_score_threshold)

        Returns:
            True if the table scores above the threshold, False otherwise
        """
        score = 0

        # Check for thead and tbody
        has_thead = len(table.xpath(".//thead")) > 0
        has_tbody = len(table.xpath(".//tbody")) > 0
        if has_thead:
            score += 2
        if has_tbody:
            score += 1

        # Check for th elements
        th_count = len(table.xpath(".//th"))
        if th_count > 0:
            score += 2
            if has_thead or table.xpath(".//tr[1]/th"):
                score += 1

        # Check for nested tables (negative indicator)
        if len(table.xpath(".//table")) > 0:
            score -= 3

        # Role attribute check
        role = table.get("role", "").lower()
        if role in {"presentation", "none"}:
            score -= 3

        # Column consistency
        rows = table.xpath(".//tr")
        if not rows:
            return False

        col_counts = [len(row.xpath(".//td|.//th")) for row in rows]
        if col_counts:
            avg_cols = sum(col_counts) / len(col_counts)
            variance = sum((c - avg_cols)**2 for c in col_counts) / len(col_counts)
            if variance < 1:
                score += 2

        # Caption and summary
        if table.xpath(".//caption"):
            score += 2
        if table.get("summary"):
            score += 1

        # Text density
        total_text = sum(
            len(''.join(cell.itertext()).strip()) 
            for row in rows 
            for cell in row.xpath(".//td|.//th")
        )
        total_tags = sum(1 for _ in table.iterdescendants())
        text_ratio = total_text / (total_tags + 1e-5)
        if text_ratio > 20:
            score += 3
        elif text_ratio > 10:
            score += 2

        # Data attributes
        data_attrs = sum(1 for attr in table.attrib if attr.startswith('data-'))
        score += data_attrs * 0.5

        # Size check
        if col_counts and len(rows) >= 2:
            avg_cols = sum(col_counts) / len(col_counts)
            if avg_cols >= 2:
                score += 2

        threshold = kwargs.get("table_score_threshold", self.table_score_threshold)
        return score >= threshold