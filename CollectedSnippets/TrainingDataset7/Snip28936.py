def test_one_to_one_field(self):
        class TestModelAdmin(ModelAdmin):
            prepopulated_fields = {"best_friend": ("name",)}

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'prepopulated_fields' refers to 'best_friend', which must "
            "not be a DateTimeField, a ForeignKey, a OneToOneField, or a "
            "ManyToManyField.",
            "admin.E028",
        )