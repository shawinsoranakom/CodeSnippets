def assertLocationCommentPresent(self, po_filename, line_number, *comment_parts):
        r"""
        self.assertLocationCommentPresent('django.po', 42, 'dirA', 'dirB',
        'foo.py')

        verifies that the django.po file has a gettext-style location comment
        of the form

        `#: dirA/dirB/foo.py:42`

        (or `#: .\dirA\dirB\foo.py:42` on Windows)

        None can be passed for the line_number argument to skip checking of
        the :42 suffix part.
        A string token can also be passed as line_number, in which case it
        will be searched in the template, and its line number will be used.
        A msgid is a suitable candidate.
        """
        return self._assertPoLocComment(True, po_filename, line_number, *comment_parts)