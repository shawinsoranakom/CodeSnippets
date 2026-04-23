def _get_cleaned_formset(cls, field_value):
        formset = cls(
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "0",
                "form-0-field": field_value,
            }
        )
        formset.full_clean()
        return formset