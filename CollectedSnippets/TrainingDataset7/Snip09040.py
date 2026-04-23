def handle_field(self, obj, field):
        """
        Handle each field on an object (except for ForeignKeys and
        ManyToManyFields).
        """
        self.indent_level += 1
        self.indent(self.indent_level)
        self.xml.startElement(
            "field",
            {
                "name": field.name,
                "type": field.get_internal_type(),
            },
        )

        # Get a "string version" of the object's data.
        if getattr(obj, field.name) is not None:
            value = field.value_to_string(obj)
            if field.get_internal_type() == "JSONField":
                # Dump value since JSONField.value_to_string() doesn't output
                # strings.
                value = json.dumps(value, cls=field.encoder)
            try:
                self.xml.characters(value)
            except UnserializableContentError:
                raise ValueError(
                    "%s.%s (pk:%s) contains unserializable characters"
                    % (obj.__class__.__name__, field.name, obj.pk)
                )
        else:
            self.xml.addQuickElement("None")

        self.xml.endElement("field")
        self.indent_level -= 1