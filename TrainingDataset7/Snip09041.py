def handle_fk_field(self, obj, field):
        """
        Handle a ForeignKey (they need to be treated slightly
        differently from regular fields).
        """
        self._start_relational_field(field)
        related_att = getattr(obj, field.attname)
        if related_att is not None:
            if self.use_natural_foreign_keys and (
                natural_key_value := self._resolve_fk_natural_key(obj, field)
            ):
                # Iterable natural keys are rolled out as subelements
                for key_value in natural_key_value:
                    self.xml.startElement("natural", {})
                    if key_value is None:
                        self.xml.addQuickElement("None")
                    else:
                        self.xml.characters(str(key_value))
                    self.xml.endElement("natural")
            else:
                self.xml.characters(str(related_att))
        else:
            self.xml.addQuickElement("None")
        self.xml.endElement("field")
        self.indent_level -= 1