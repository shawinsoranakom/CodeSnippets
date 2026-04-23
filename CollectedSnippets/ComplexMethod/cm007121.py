def is_table(self, text):
        rows = text.split("\n")
        if len(rows) < MIN_ROWS_IN_TABLE:
            return False

        has_separator = False
        for i, row in enumerate(rows):
            if "|" in row:
                cells = [cell.strip() for cell in row.split("|")]
                cells = [cell for cell in cells if cell]  # Remove empty cells
                if i == 1 and all(set(cell) <= set("-|") for cell in cells):
                    has_separator = True
                elif not cells:
                    return False

        return has_separator