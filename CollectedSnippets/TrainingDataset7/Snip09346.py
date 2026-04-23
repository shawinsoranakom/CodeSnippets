def format_json_path_numeric_index(self, num):
        """
        Hook for backends to customize array indexing in JSON paths.
        """
        return "[%s]" % num