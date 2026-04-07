def clean(self, value):
        if value in self.empty_values:
            if self.pk_field:
                return None
            # if there is no value act as we did before.
            return self.parent_instance
        # ensure the we compare the values as equal types.
        if self.to_field:
            orig = getattr(self.parent_instance, self.to_field)
        else:
            orig = self.parent_instance.pk
        if str(value) != str(orig):
            raise ValidationError(
                self.error_messages["invalid_choice"], code="invalid_choice"
            )
        return self.parent_instance