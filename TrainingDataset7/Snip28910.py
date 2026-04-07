def test_invalid_type(self):
        class FakeForm:
            pass

        class TestModelAdmin(ModelAdmin):
            form = FakeForm

        class TestModelAdminWithNoForm(ModelAdmin):
            form = "not a form"

        for model_admin in (TestModelAdmin, TestModelAdminWithNoForm):
            with self.subTest(model_admin):
                self.assertIsInvalid(
                    model_admin,
                    ValidationTestModel,
                    "The value of 'form' must inherit from 'BaseModelForm'.",
                    "admin.E016",
                )