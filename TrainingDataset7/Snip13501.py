def resolve_template(self, template):
        """Accept a template object, path-to-template, or list of paths."""
        if isinstance(template, (list, tuple)):
            return select_template(template, using=self.using)
        elif isinstance(template, str):
            return get_template(template, using=self.using)
        else:
            return template