def test_no_dtd(self):
        """
        The XML deserializer shouldn't allow a DTD.

        This is the most straightforward way to prevent all entity definitions
        and avoid both external entities and entity-expansion attacks.
        """
        xml = (
            '<?xml version="1.0" standalone="no"?>'
            '<!DOCTYPE example SYSTEM "http://example.com/example.dtd">'
        )
        with self.assertRaises(DTDForbidden):
            next(serializers.deserialize("xml", xml))