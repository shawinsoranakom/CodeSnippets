def errors(self):
        return mark_safe(
            "\n".join(
                self.form[f].errors.as_ul()
                for f in self.fields
                if f not in self.readonly_fields
            ).strip("\n")
        )