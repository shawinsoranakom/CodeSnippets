def write(self, outfile, encoding):
        handler = SimplerXMLGenerator(outfile, encoding, short_empty_elements=True)
        handler.startDocument()
        handler.startElement("feed", self.root_attributes())
        self.add_root_elements(handler)
        self.write_items(handler)
        handler.endElement("feed")