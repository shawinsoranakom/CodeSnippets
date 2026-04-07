def pk_field(self):
        return AdminField(self.form, self.formset._pk_field.name, False)