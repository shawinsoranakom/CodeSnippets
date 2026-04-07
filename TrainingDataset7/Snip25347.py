def test_id_clash(self):
        class Target(models.Model):
            pass

        class Model(models.Model):
            fk = models.ForeignKey(Target, models.CASCADE)
            fk_id = models.IntegerField()

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "The field 'fk_id' clashes with the field 'fk' from model "
                    "'invalid_models_tests.model'.",
                    obj=Model._meta.get_field("fk_id"),
                    id="models.E006",
                )
            ],
        )