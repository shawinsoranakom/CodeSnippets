def test_pk(self):
        class Model(models.Model):
            pk = models.IntegerField()

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'pk' is a reserved word that cannot be used as a field name.",
                    obj=Model._meta.get_field("pk"),
                    id="fields.E003",
                )
            ],
        )