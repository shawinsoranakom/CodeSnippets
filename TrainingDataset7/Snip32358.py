def render_template(self, template, **kwargs):
        if isinstance(template, str):
            template = Template(template)
        return template.render(Context(**kwargs)).strip()