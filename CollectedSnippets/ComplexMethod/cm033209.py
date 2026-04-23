def _print_table_simple(self, data):
        if not data:
            print("No data to print")
            return
        if isinstance(data, dict):
            # handle single row data
            data = [data]

        columns = list(set().union(*(d.keys() for d in data)))
        columns.sort()
        col_widths = {}

        def get_string_width(text):
            half_width_chars = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\t\n\r"
            width = 0
            for char in text:
                if char in half_width_chars:
                    width += 1
                else:
                    width += 2
            return width

        for col in columns:
            max_width = get_string_width(str(col))
            for item in data:
                value_len = get_string_width(str(item.get(col, "")))
                if value_len > max_width:
                    max_width = value_len
            col_widths[col] = max(2, max_width)

        # Generate delimiter
        separator = "+" + "+".join(["-" * (col_widths[col] + 2) for col in columns]) + "+"

        # Print header
        print(separator)
        header = "|" + "|".join([f" {col:<{col_widths[col]}} " for col in columns]) + "|"
        print(header)
        print(separator)

        # Print data
        for item in data:
            row = "|"
            for col in columns:
                value = str(item.get(col, ""))
                if get_string_width(value) > col_widths[col]:
                    value = value[: col_widths[col] - 3] + "..."
                row += f" {value:<{col_widths[col] - (get_string_width(value) - len(value))}} |"
            print(row)

        print(separator)