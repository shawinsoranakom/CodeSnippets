def end_object(self, obj):
        """
        Called after handling all fields for an object.
        """
        self.indent(self.indent_level)
        self.xml.endElement("object")
        self.indent_level -= 1