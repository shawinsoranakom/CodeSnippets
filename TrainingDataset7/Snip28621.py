def add_fields(self, form, index):
        super().add_fields(form, index)
        self.can_delete = True
        if DELETION_FIELD_NAME in form.fields:
            del form.fields[DELETION_FIELD_NAME]