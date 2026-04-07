def from_string(self, template_code):
        return Template(self.env.from_string(template_code), self)