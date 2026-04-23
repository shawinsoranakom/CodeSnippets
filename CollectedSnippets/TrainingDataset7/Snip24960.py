def _assertPoLocComment(
        self, assert_presence, po_filename, line_number, *comment_parts
    ):
        with open(po_filename) as fp:
            po_contents = fp.read()
        if os.name == "nt":
            # #: .\path\to\file.html:123
            cwd_prefix = "%s%s" % (os.curdir, os.sep)
        else:
            # #: path/to/file.html:123
            cwd_prefix = ""

        path = os.path.join(cwd_prefix, *comment_parts)
        parts = [path]

        if isinstance(line_number, str):
            line_number = self._get_token_line_number(path, line_number)
        if line_number is not None:
            parts.append(":%d" % line_number)

        needle = "".join(parts)
        pattern = re.compile(r"^\#\:.*" + re.escape(needle), re.MULTILINE)
        if assert_presence:
            return self.assertRegex(
                po_contents, pattern, '"%s" not found in final .po file.' % needle
            )
        else:
            return self.assertNotRegex(
                po_contents, pattern, '"%s" shouldn\'t be in final .po file.' % needle
            )