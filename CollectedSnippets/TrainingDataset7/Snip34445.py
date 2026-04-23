def test_template_without_extra_data_attribute(self):
        partial_name = "some_partial_name"
        with (
            self.override_get_template(),
            self.assertRaisesMessage(TemplateDoesNotExist, partial_name),
        ):
            engine.get_template(f"some_template.html#{partial_name}")