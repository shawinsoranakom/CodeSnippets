def tag(self, wrap_label=False):
        context = {"widget": {**self.data, "wrap_label": wrap_label}}
        return self.parent_widget._render(self.template_name, context, self.renderer)