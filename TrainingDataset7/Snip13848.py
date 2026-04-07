def rendered_template_names(self):
        return [
            (
                f"{t.origin.template_name}#{t.name}"
                if isinstance(t, PartialTemplate)
                else t.name
            )
            for t in self.rendered_templates
            if t.name is not None
        ]