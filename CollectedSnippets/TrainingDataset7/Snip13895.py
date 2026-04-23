def assertXMLNotEqual(self, xml1, xml2, msg=None):
        """
        Assert that two XML snippets are not semantically equivalent.
        Whitespace in most cases is ignored and attribute ordering is not
        significant. The arguments must be valid XML.
        """
        try:
            result = compare_xml(xml1, xml2)
        except Exception as e:
            standardMsg = "First or second argument is not valid XML\n%s" % e
            self.fail(self._formatMessage(msg, standardMsg))
        else:
            if result:
                standardMsg = "%s == %s" % (
                    safe_repr(xml1, True),
                    safe_repr(xml2, True),
                )
                self.fail(self._formatMessage(msg, standardMsg))