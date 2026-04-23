def format_json_path_numeric_index(self, num):
        if num < 0:
            return "[last-%s]" % abs(num + 1)  # Indexing is zero-based.
        return super().format_json_path_numeric_index(num)