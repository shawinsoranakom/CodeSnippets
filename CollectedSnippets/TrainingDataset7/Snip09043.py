def _start_relational_field(self, field):
        """Output the <field> element for relational fields."""
        self.indent_level += 1
        self.indent(self.indent_level)
        self.xml.startElement(
            "field",
            {
                "name": field.name,
                "rel": field.remote_field.__class__.__name__,
                "to": str(field.remote_field.model._meta),
            },
        )