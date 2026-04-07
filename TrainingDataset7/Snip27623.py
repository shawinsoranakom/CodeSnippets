def test_explicit_index_name(self):
        class TestModel(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "migrations"
                indexes = [models.Index(fields=["name"], name="foo_idx")]

        model_state = ModelState.from_model(TestModel)
        index_names = [index.name for index in model_state.options["indexes"]]
        self.assertEqual(index_names, ["foo_idx"])