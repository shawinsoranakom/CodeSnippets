def start_serialization(self):
        """
        Start serialization -- open the XML document and the root element.
        """
        # Increment the indent_level before each startElement() and decrement
        # it following each endElement(). If the closing tag should appear on
        # its own line, use self.indent(self.indent_level) before endElement().
        self.indent_level = 0
        self.xml = SimplerXMLGenerator(
            self.stream, self.options.get("encoding", settings.DEFAULT_CHARSET)
        )
        self.xml.startDocument()
        self.xml.startElement("django-objects", {"version": "1.0"})