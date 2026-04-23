def test_including_separator(self):
        class Model(models.Model):
            some__field = models.IntegerField()

        self.assertEqual(
            Model.check(),
            [
                Error(
                    'Field names must not contain "__".',
                    obj=Model._meta.get_field("some__field"),
                    id="fields.E002",
                )
            ],
        )