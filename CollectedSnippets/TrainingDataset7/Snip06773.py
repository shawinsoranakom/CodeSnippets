def formfield(self, **kwargs):
        defaults = {
            "form_class": self.form_class,
            "geom_type": self.geom_type,
            "srid": self.srid,
            **kwargs,
        }
        if self.dim > 2 and not getattr(
            defaults["form_class"].widget, "supports_3d", False
        ):
            defaults.setdefault("widget", forms.Textarea)
        return super().formfield(**defaults)