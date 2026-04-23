def assertLocationCommentNotPresent(self, po_filename, line_number, *comment_parts):
        """Check the opposite of assertLocationComment()"""
        return self._assertPoLocComment(False, po_filename, line_number, *comment_parts)