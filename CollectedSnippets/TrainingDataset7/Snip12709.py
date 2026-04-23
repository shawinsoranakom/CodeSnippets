def render(self, template_name=None, context=None, renderer=None):
        renderer = renderer or self.renderer
        template = template_name or self.template_name
        context = context or self.get_context()
        return mark_safe(renderer.render(template, context))