def deletion_field(self):
        from django.forms.formsets import DELETION_FIELD_NAME

        return AdminField(self.form, DELETION_FIELD_NAME, False)