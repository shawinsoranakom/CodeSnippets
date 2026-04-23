def get_exception_info(self, exception, token):
        """
        Return a dictionary containing contextual line information of where
        the exception occurred in the template. The following information is
        provided:

        message
            The message of the exception raised.

        source_lines
            The lines before, after, and including the line the exception
            occurred on.

        line
            The line number the exception occurred on.

        before, during, after
            The line the exception occurred on split into three parts:
            1. The content before the token that raised the error.
            2. The token that raised the error.
            3. The content after the token that raised the error.

        total
            The number of lines in source_lines.

        top
            The line number where source_lines starts.

        bottom
            The line number where source_lines ends.

        start
            The start position of the token in the template source.

        end
            The end position of the token in the template source.
        """
        start, end = token.position
        context_lines = 10
        line = 0
        upto = 0
        source_lines = []
        before = during = after = ""
        for num, next in enumerate(linebreak_iter(self.source)):
            if start >= upto and end <= next:
                line = num
                before = self.source[upto:start]
                during = self.source[start:end]
                after = self.source[end:next]
            source_lines.append((num, self.source[upto:next]))
            upto = next
        total = len(source_lines)

        top = max(1, line - context_lines)
        bottom = min(total, line + 1 + context_lines)

        # In some rare cases exc_value.args can be empty or an invalid
        # string.
        try:
            message = str(exception.args[0])
        except (IndexError, UnicodeDecodeError):
            message = "(Could not get exception message)"

        return {
            "message": message,
            "source_lines": source_lines[top:bottom],
            "before": before,
            "during": during,
            "after": after,
            "top": top,
            "bottom": bottom,
            "total": total,
            "line": line,
            "name": self.origin.name,
            "start": start,
            "end": end,
        }