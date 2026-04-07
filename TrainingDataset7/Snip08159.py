def get_comment_blocks(self, content, include_line_comments=False):
        """
        Return a list of (start, end) tuples for each comment block.
        """
        pattern = line_comment_re if include_line_comments else comment_re
        return [(match.start(), match.end()) for match in re.finditer(pattern, content)]