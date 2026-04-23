def render(self, context):
        """
        Render the specified template and context. Cache the template object
        in render_context to avoid reparsing and loading when used in a for
        loop.
        """
        template = self.template.resolve(context)
        # Does this quack like a Template?
        if not callable(getattr(template, "render", None)):
            # If not, try the cache and select_template().
            template_name = template or ()
            if isinstance(template_name, str):
                template_name = (
                    construct_relative_path(
                        self.origin.template_name,
                        template_name,
                    ),
                )
            else:
                template_name = tuple(template_name)
            cache = context.render_context.dicts[0].setdefault(self, {})
            template = cache.get(template_name)
            if template is None:
                template = context.template.engine.select_template(template_name)
                cache[template_name] = template
        # Use the base.Template of a backends.django.Template.
        elif hasattr(template, "template"):
            template = template.template
        values = {
            name: var.resolve(context) for name, var in self.extra_context.items()
        }
        if self.isolated_context:
            return template.render(context.new(values))
        with context.push(**values):
            return template.render(context)