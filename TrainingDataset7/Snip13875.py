def _form_repr(self, form, formset, form_index):
        if formset is None:
            return f"form {form!r}"
        return f"form {form_index} of formset {formset!r}"