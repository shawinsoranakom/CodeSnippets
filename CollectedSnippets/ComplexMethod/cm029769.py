def _find_lineno(self, obj, source_lines):
        """
        Return a line number of the given object's docstring.

        Returns `None` if the given object does not have a docstring.
        """
        lineno = None
        docstring = getattr(obj, '__doc__', None)

        # Find the line number for modules.
        if inspect.ismodule(obj) and docstring is not None:
            lineno = 0

        # Find the line number for classes.
        # Note: this could be fooled if a class is defined multiple
        # times in a single file.
        if inspect.isclass(obj) and docstring is not None:
            if source_lines is None:
                return None
            pat = re.compile(r'^\s*class\s*%s\b' %
                             re.escape(getattr(obj, '__name__', '-')))
            for i, line in enumerate(source_lines):
                if pat.match(line):
                    lineno = i
                    break

        # Find the line number for functions & methods.
        if inspect.ismethod(obj): obj = obj.__func__
        if isinstance(obj, property):
            obj = obj.fget
        if isinstance(obj, functools.cached_property):
            obj = obj.func
        if inspect.isroutine(obj) and getattr(obj, '__doc__', None):
            # We don't use `docstring` var here, because `obj` can be changed.
            obj = inspect.unwrap(obj)
            try:
                obj = obj.__code__
            except AttributeError:
                # Functions implemented in C don't necessarily
                # have a __code__ attribute.
                # If there's no code, there's no lineno
                return None
        if inspect.istraceback(obj): obj = obj.tb_frame
        if inspect.isframe(obj): obj = obj.f_code
        if inspect.iscode(obj):
            lineno = obj.co_firstlineno - 1

        # Find the line number where the docstring starts.  Assume
        # that it's the first line that begins with a quote mark.
        # Note: this could be fooled by a multiline function
        # signature, where a continuation line begins with a quote
        # mark.
        if lineno is not None:
            if source_lines is None:
                return lineno+1
            pat = re.compile(r'(^|.*:)\s*\w*("|\')')
            for lineno in range(lineno, len(source_lines)):
                if pat.match(source_lines[lineno]):
                    return lineno

        # Handle __test__ string doctests formatted as triple-quoted
        # strings. Find a non-blank line in the test string and match it
        # in the source, verifying subsequent lines also match to handle
        # duplicate lines.
        if isinstance(obj, str) and source_lines is not None:
            obj_lines = obj.splitlines(keepends=True)
            # Skip the first line (may be on same line as opening quotes)
            # and any blank lines to find a meaningful line to match.
            start_index = 1
            while (start_index < len(obj_lines)
                   and not obj_lines[start_index].strip()):
                start_index += 1
            if start_index < len(obj_lines):
                target_line = obj_lines[start_index]
                for lineno, source_line in enumerate(source_lines):
                    if source_line == target_line:
                        # Verify subsequent lines also match
                        for i in range(start_index + 1, len(obj_lines) - 1):
                            source_idx = lineno + i - start_index
                            if source_idx >= len(source_lines):
                                break
                            if obj_lines[i] != source_lines[source_idx]:
                                break
                        else:
                            return lineno - start_index

        # We couldn't find the line number.
        return None