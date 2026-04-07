def as_ul(self):
        """Render as <li> elements excluding the surrounding <ul> tag."""
        return self.render(self.template_name_ul)