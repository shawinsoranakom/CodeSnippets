def from_string(self, template_code):
        return Template(self.engine.from_string(template_code), self)