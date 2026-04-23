def test_valid_field(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=255,
                choices=[
                    ("1", "item1"),
                    ("2", "item2"),
                ],
                db_index=True,
            )

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(), [])