def test_choices_named_group(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=10,
                choices=[
                    ["knights", [["L", "Lancelot"], ["G", "Galahad"]]],
                    ["wizards", [["T", "Tim the Enchanter"]]],
                    ["R", "Random character"],
                ],
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])