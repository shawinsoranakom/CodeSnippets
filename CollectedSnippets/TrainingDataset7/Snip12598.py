def empty_form(self):
        form_kwargs = {
            **self.get_form_kwargs(None),
            "auto_id": self.auto_id,
            "prefix": self.add_prefix("__prefix__"),
            "empty_permitted": True,
            "use_required_attribute": False,
            "renderer": self.form_renderer,
        }
        form = self.form(**form_kwargs)
        self.add_fields(form, None)
        return form