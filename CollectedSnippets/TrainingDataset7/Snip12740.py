def __str__(self):
        return format_html(
            self.element_template,
            path=self.path,
            attributes=flatatt(self.attributes),
        )