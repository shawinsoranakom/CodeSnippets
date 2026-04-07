def test_valid_expression(self):
        class TestModelAdmin(ModelAdmin):
            ordering = (Upper("name"), Upper("band__name").desc())

        self.assertIsValid(TestModelAdmin, ValidationTestModel)