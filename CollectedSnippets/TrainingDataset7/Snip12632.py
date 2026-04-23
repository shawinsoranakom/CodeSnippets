def _get_validation_exclusions(self):
        """
        For backwards-compatibility, exclude several types of fields from model
        validation. See tickets #12507, #12521, #12553.
        """
        exclude = set()
        # Build up a list of fields that should be excluded from model field
        # validation and unique checks.
        for f in self.instance._meta.fields:
            field = f.name
            # Exclude fields that aren't on the form. The developer may be
            # adding these values to the model after form validation.
            if field not in self.fields:
                exclude.add(f.name)

            # Don't perform model validation on fields that were defined
            # manually on the form and excluded via the ModelForm's Meta
            # class. See #12901.
            elif self._meta.fields and field not in self._meta.fields:
                exclude.add(f.name)
            elif self._meta.exclude and field in self._meta.exclude:
                exclude.add(f.name)

            # Exclude fields that failed form validation. There's no need for
            # the model fields to validate them as well.
            elif field in self._errors:
                exclude.add(f.name)

            # Exclude empty fields that are not required by the form, if the
            # underlying model field is required. This keeps the model field
            # from raising a required error. Note: don't exclude the field from
            # validation if the model field allows blanks. If it does, the
            # blank value may be included in a unique check, so cannot be
            # excluded from validation.
            else:
                form_field = self.fields[field]
                field_value = self.cleaned_data.get(field)
                if (
                    not f.blank
                    and not form_field.required
                    and field_value in form_field.empty_values
                ):
                    exclude.add(f.name)
        return exclude