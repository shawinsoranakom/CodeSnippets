def __init__(self, form, field, name):
        self.form = form
        self.field = field
        self.name = name
        self.html_name = form.add_prefix(name)
        self.html_initial_name = form.add_initial_prefix(name)
        self.html_initial_id = form.add_initial_prefix(self.auto_id)
        if self.field.label is None:
            self.label = pretty_name(name)
        else:
            self.label = self.field.label
        self.help_text = field.help_text or ""
        self.renderer = form.renderer