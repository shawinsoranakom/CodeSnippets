def on_template_render(self, sender, signal, template, context, **kwargs):
        self.rendered_templates.append(template)
        self.context.append(copy(context))