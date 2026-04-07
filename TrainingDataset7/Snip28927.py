def test_invalid_field_type(self):
        class TestModelAdmin(ModelAdmin):
            radio_fields = {"name": VERTICAL}

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'radio_fields' refers to 'name', which is not an instance "
            "of ForeignKey, and does not have a 'choices' definition.",
            "admin.E023",
        )