def assertMultiLineEqual(self, first, second, msg=None):
        """Assert that two multi-line strings are equal."""
        self.assertIsInstance(first, str, "First argument is not a string")
        self.assertIsInstance(second, str, "Second argument is not a string")

        if first != second:
            # Don't use difflib if the strings are too long
            if (len(first) > self._diffThreshold or
                len(second) > self._diffThreshold):
                self._baseAssertEqual(first, second, msg)

            # Append \n to both strings if either is missing the \n.
            # This allows the final ndiff to show the \n difference. The
            # exception here is if the string is empty, in which case no
            # \n should be added
            first_presplit = first
            second_presplit = second
            if first and second:
                if first[-1] != '\n' or second[-1] != '\n':
                    first_presplit += '\n'
                    second_presplit += '\n'
            elif second and second[-1] != '\n':
                second_presplit += '\n'
            elif first and first[-1] != '\n':
                first_presplit += '\n'

            firstlines = first_presplit.splitlines(keepends=True)
            secondlines = second_presplit.splitlines(keepends=True)

            # Generate the message and diff, then raise the exception
            standardMsg = '%s != %s' % _common_shorten_repr(first, second)
            diff = '\n' + ''.join(difflib.ndiff(firstlines, secondlines))
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))