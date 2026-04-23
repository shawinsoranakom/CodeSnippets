def handle_table(self, html, doc):
        """
        To handle nested tables, we will parse tables manually as follows:
        Get table soup
        Create docx table
        Iterate over soup and fill docx table with new instances of this parser
        Tell HTMLParser to ignore any tags until the corresponding closing table tag
        """
        table_soup = BeautifulSoup(html, "html.parser")
        rows, cols_len = get_table_dimensions(table_soup)
        table = doc.add_table(len(rows), cols_len)
        table.style = doc.styles["Table Grid"]

        num_rows = len(table.rows)
        num_cols = len(table.columns)

        cell_row = 0
        for index, row in enumerate(rows):
            cols = get_table_columns(row)
            cell_col = 0
            for col in cols:
                colspan = int(col.attrs.get("colspan", 1))
                rowspan = int(col.attrs.get("rowspan", 1))

                cell_html = get_cell_html(col)
                if col.name == "th":
                    cell_html = "<b>%s</b>" % cell_html

                if cell_row >= num_rows or cell_col >= num_cols:
                    continue

                docx_cell = table.cell(cell_row, cell_col)

                while docx_cell.text != "":  # Skip the merged cell
                    cell_col += 1
                    docx_cell = table.cell(cell_row, cell_col)

                cell_to_merge = table.cell(
                    cell_row + rowspan - 1, cell_col + colspan - 1
                )
                if docx_cell != cell_to_merge:
                    docx_cell.merge(cell_to_merge)

                child_parser = HtmlToDocx()
                child_parser.copy_settings_from(self)
                child_parser.add_html_to_cell(cell_html or " ", docx_cell)

                cell_col += colspan
            cell_row += 1