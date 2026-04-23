def test_swappable_missing_app_name(self):
        class Model(models.Model):
            class Meta:
                swappable = "TEST_SWAPPED_MODEL_BAD_VALUE"

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'TEST_SWAPPED_MODEL_BAD_VALUE' is not of the form "
                    "'app_label.app_name'.",
                    id="models.E001",
                ),
            ],
        )