def get_context(self):
        fields = []
        hidden_fields = []
        top_errors = self.non_field_errors().copy()
        for name, bf in self._bound_items():
            if bf.is_hidden:
                if bf.errors:
                    top_errors += [
                        _("(Hidden field %(name)s) %(error)s")
                        % {"name": name, "error": str(e)}
                        for e in bf.errors
                    ]
                hidden_fields.append(bf)
            else:
                fields.append((bf, bf.errors))
        return {
            "form": self,
            "fields": fields,
            "hidden_fields": hidden_fields,
            "errors": top_errors,
        }