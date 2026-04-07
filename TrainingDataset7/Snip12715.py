def as_table(self):
        """Render as <tr> elements excluding the surrounding <table> tag."""
        return self.render(self.template_name_table)