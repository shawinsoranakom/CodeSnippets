def _check_error(self, code, errtext,
                     filename="<testcase>", mode="exec", subclass=None,
                     lineno=None, offset=None, end_lineno=None, end_offset=None):
        """Check that compiling code raises SyntaxError with errtext.

        errtest is a regular expression that must be present in the
        text of the exception raised.  If subclass is specified it
        is the expected subclass of SyntaxError (e.g. IndentationError).
        """
        try:
            compile(code, filename, mode)
        except SyntaxError as err:
            if subclass and not isinstance(err, subclass):
                self.fail("SyntaxError is not a %s" % subclass.__name__)
            mo = re.search(errtext, str(err))
            if mo is None:
                self.fail("SyntaxError did not contain %r" % (errtext,))
            self.assertEqual(err.filename, filename)
            if lineno is not None:
                self.assertEqual(err.lineno, lineno)
            if offset is not None:
                self.assertEqual(err.offset, offset)
            if end_lineno is not None:
                self.assertEqual(err.end_lineno, end_lineno)
            if end_offset is not None:
                self.assertEqual(err.end_offset, end_offset)

        else:
            self.fail("compile() did not raise SyntaxError")