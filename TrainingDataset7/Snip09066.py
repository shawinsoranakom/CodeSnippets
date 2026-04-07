def handle_m2m(value):
                    if natural := self._resolve_natural_key(value):
                        # Iterable natural keys are rolled out as subelements
                        self.xml.startElement("object", {})
                        for key_value in natural:
                            self.xml.startElement("natural", {})
                            if key_value is None:
                                self.xml.addQuickElement("None")
                            else:
                                self.xml.characters(str(key_value))
                            self.xml.endElement("natural")
                        self.xml.endElement("object")
                    else:
                        self.xml.addQuickElement("object", attrs={"pk": str(value.pk)})