def test_name_contains_double_underscores(self):
        class Test__Model(models.Model):
            pass

        self.assertEqual(
            Test__Model.check(),
            [
                Error(
                    "The model name 'Test__Model' cannot contain double underscores "
                    "as it collides with the query lookup syntax.",
                    obj=Test__Model,
                    id="models.E024",
                )
            ],
        )