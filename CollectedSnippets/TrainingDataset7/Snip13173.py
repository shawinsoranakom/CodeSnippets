def source(self):
        template = self.origin.loader.get_template(self.origin.template_name)
        if not template.engine.debug:
            warnings.warn(
                "PartialTemplate.source is only available when template "
                "debugging is enabled.",
                RuntimeWarning,
                skip_file_prefixes=django_file_prefixes(),
            )
        return self.find_partial_source(template.source)