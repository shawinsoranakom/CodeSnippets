def assert_xml_contains_datetime(self, xml, dt):
        field = parseString(xml).getElementsByTagName("field")[0]
        self.assertXMLEqual(field.childNodes[0].wholeText, dt)