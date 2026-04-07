def _assertPoKeyword(self, keyword, expected_value, haystack, use_quotes=True):
        q = '"'
        if use_quotes:
            expected_value = '"%s"' % expected_value
            q = "'"
        needle = "%s %s" % (keyword, expected_value)
        expected_value = re.escape(expected_value)
        return self.assertTrue(
            re.search("^%s %s" % (keyword, expected_value), haystack, re.MULTILINE),
            "Could not find %(q)s%(n)s%(q)s in generated PO file"
            % {"n": needle, "q": q},
        )