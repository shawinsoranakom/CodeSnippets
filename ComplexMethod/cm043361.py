def _extract_table_structure(self, html_content: str) -> Tuple[List[etree.Element], List[etree.Element], List[etree.Element], bool]:
        """
        Extract headers, body rows, and footer from table HTML.

        Returns:
            Tuple of (header_rows, body_rows, footer_rows, has_headers)
        """
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_content, parser)

        # Find all tables
        tables = tree.xpath('.//table')
        if not tables:
            return [], [], [], False

        table = tables[0]  # Process first table

        # Extract header rows (from thead or first rows with th)
        header_rows = []
        thead = table.xpath('.//thead')
        if thead:
            header_rows = thead[0].xpath('.//tr')
        else:
            # Look for rows with th elements
            for row in table.xpath('.//tr'):
                if row.xpath('.//th'):
                    header_rows.append(row)
                else:
                    break

        # Track if we found headers
        has_headers = len(header_rows) > 0

        # Extract footer rows
        footer_rows = []
        tfoot = table.xpath('.//tfoot')
        if tfoot:
            footer_rows = tfoot[0].xpath('.//tr')

        # Extract body rows
        body_rows = []
        tbody = table.xpath('.//tbody')
        if tbody:
            body_rows = tbody[0].xpath('.//tr')
        else:
            # Get all rows that aren't headers or footers
            all_rows = table.xpath('.//tr')
            header_count = len(header_rows)
            footer_count = len(footer_rows)

            if footer_count > 0:
                body_rows = all_rows[header_count:-footer_count]
            else:
                body_rows = all_rows[header_count:]

        # If no headers found and no tbody, all rows are body rows
        if not has_headers and not tbody:
            body_rows = tables[0].xpath('.//tr')

        return header_rows, body_rows, footer_rows, has_headers