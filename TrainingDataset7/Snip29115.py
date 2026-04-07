def build_attrs(self, base_attrs, extra_attrs=None):
                attrs = super().build_attrs(base_attrs, extra_attrs)
                attrs["use_fieldset"] = "true"
                return attrs