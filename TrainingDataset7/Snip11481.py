def formfield(self, *, using=None, **kwargs):
        defaults = {
            "form_class": forms.ModelMultipleChoiceField,
            "queryset": self.remote_field.model._default_manager.using(using),
            **kwargs,
        }
        # If initial is passed in, it's a list of related objects, but the
        # MultipleChoiceField takes a list of IDs.
        if defaults.get("initial") is not None:
            initial = defaults["initial"]
            if callable(initial):
                initial = initial()
            defaults["initial"] = [i.pk for i in initial]
        return super().formfield(**defaults)