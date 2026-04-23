def _get_lines_from_file(
        self, filename, lineno, context_lines, loader=None, module_name=None
    ):
        """
        Return context_lines before and after lineno from file.
        Return (pre_context_lineno, pre_context, context_line, post_context).
        """
        source = self._get_source(filename, loader, module_name)
        if source is None:
            return None, [], None, []

        # If we just read the source from a file, or if the loader did not
        # apply tokenize.detect_encoding to decode the source into a
        # string, then we should do that ourselves.
        if isinstance(source[0], bytes):
            encoding = "ascii"
            for line in source[:2]:
                # File coding may be specified. Match pattern from PEP-263
                # (https://www.python.org/dev/peps/pep-0263/)
                match = re.search(rb"coding[:=]\s*([-\w.]+)", line)
                if match:
                    encoding = match[1].decode("ascii")
                    break
            source = [str(sline, encoding, "replace") for sline in source]

        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        try:
            pre_context = source[lower_bound:lineno]
            context_line = source[lineno]
            post_context = source[lineno + 1 : upper_bound]
        except IndexError:
            return None, [], None, []
        return lower_bound, pre_context, context_line, post_context