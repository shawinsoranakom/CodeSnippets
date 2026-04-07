def test_fields_for_model_form_fields(self):
        form_declared_fields = CustomWriterForm.declared_fields
        field_dict = fields_for_model(
            Writer,
            fields=["name"],
            form_declared_fields=form_declared_fields,
        )
        self.assertIs(field_dict["name"], form_declared_fields["name"])