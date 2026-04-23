def _get_cleaned_form(cls, field_value):
        form = cls({"field": field_value})
        form.full_clean()
        return form