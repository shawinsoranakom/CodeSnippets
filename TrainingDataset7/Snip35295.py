def test_processing_instruction(self):
        xml1 = (
            '<?xml version="1.0"?>'
            '<?xml-model href="http://www.example1.com"?><root />'
        )
        xml2 = (
            '<?xml version="1.0"?>'
            '<?xml-model href="http://www.example2.com"?><root />'
        )
        self.assertXMLEqual(xml1, xml2)
        self.assertXMLEqual(
            '<?xml-stylesheet href="style1.xslt" type="text/xsl"?><root />',
            '<?xml-stylesheet href="style2.xslt" type="text/xsl"?><root />',
        )