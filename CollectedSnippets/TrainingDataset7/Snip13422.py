def get_template(self, template_name):
        """
        Return a compiled Template object for the given template name,
        handling template inheritance recursively.
        """
        original_name = template_name
        try:
            template_name, _, partial_name = template_name.partition("#")
        except AttributeError:
            raise TemplateDoesNotExist(original_name)

        if not template_name:
            raise TemplateDoesNotExist(original_name)

        template, origin = self.find_template(template_name)
        if not hasattr(template, "render"):
            # template needs to be compiled
            template = Template(template, origin, template_name, engine=self)

        if not partial_name:
            return template

        extra_data = getattr(template, "extra_data", {})
        try:
            partial = extra_data["partials"][partial_name]
        except (KeyError, TypeError):
            raise TemplateDoesNotExist(partial_name, tried=[template_name])
        partial.engine = self

        return partial