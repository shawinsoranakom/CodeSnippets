def test_swappable_missing_app(self):
        class Model(models.Model):
            class Meta:
                swappable = "TEST_SWAPPED_MODEL_BAD_MODEL"

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'TEST_SWAPPED_MODEL_BAD_MODEL' references 'not_an_app.Target', "
                    "which has not been installed, or is abstract.",
                    id="models.E002",
                ),
            ],
        )