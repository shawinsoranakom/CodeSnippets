def handle_m2m(value):
                    # Put each object on its own line.
                    self.indent(self.indent_level + 1)
                    self.xml.addQuickElement("object", attrs={"pk": str(value.pk)})