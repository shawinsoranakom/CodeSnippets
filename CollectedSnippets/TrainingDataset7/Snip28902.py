def test_second_element_of_item_not_a_dict(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = (("General", ()),)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fieldsets[0][1]' must be a dictionary.",
            "admin.E010",
        )