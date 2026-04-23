def test_doctype_root(self):
        xml1 = '<?xml version="1.0"?><!DOCTYPE root SYSTEM "example1.dtd"><root />'
        xml2 = '<?xml version="1.0"?><!DOCTYPE root SYSTEM "example2.dtd"><root />'
        self.assertXMLEqual(xml1, xml2)