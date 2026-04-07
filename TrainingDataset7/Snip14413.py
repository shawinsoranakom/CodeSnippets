def write(self, outfile, encoding):
        handler = SimplerXMLGenerator(outfile, encoding, short_empty_elements=True)
        handler.startDocument()
        # Any stylesheet must come after the start of the document but before
        # any tag. https://www.w3.org/Style/styling-XML.en.html
        self.add_stylesheets(handler)
        handler.startElement("rss", self.rss_attributes())
        handler.startElement("channel", self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        self.endChannelElement(handler)
        handler.endElement("rss")