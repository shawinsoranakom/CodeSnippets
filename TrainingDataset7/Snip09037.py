def end_serialization(self):
        """
        End serialization -- end the document.
        """
        self.indent(self.indent_level)
        self.xml.endElement("django-objects")
        self.xml.endDocument()