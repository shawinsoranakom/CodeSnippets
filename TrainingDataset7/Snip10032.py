def format_json_path_numeric_index(self, num):
        return "[#%s]" % num if num < 0 else super().format_json_path_numeric_index(num)