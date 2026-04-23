def test_name_beginning_with_underscore(self):
        class _Model(models.Model):
            pass

        self.assertEqual(
            _Model.check(),
            [
                Error(
                    "The model name '_Model' cannot start or end with an underscore "
                    "as it collides with the query lookup syntax.",
                    obj=_Model,
                    id="models.E023",
                )
            ],
        )