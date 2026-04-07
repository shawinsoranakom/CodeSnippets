def _clean_fields(self):
        for name, bf in self._bound_items():
            field = bf.field
            try:
                self.cleaned_data[name] = field._clean_bound_field(bf)
                if hasattr(self, "clean_%s" % name):
                    value = getattr(self, "clean_%s" % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)