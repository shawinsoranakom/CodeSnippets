def _create_model_class(self, class_name, get_absolute_url_method=None):
        attrs = {
            "name": models.CharField(max_length=50),
            "__module__": "absolute_url_overrides",
        }
        if get_absolute_url_method:
            attrs["get_absolute_url"] = get_absolute_url_method

        return type(class_name, (models.Model,), attrs)