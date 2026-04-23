def test_func_index_pointing_to_composite_primary_key(self):
        class Model(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

            class Meta:
                indexes = [models.Index(Abs("pk"), name="name")]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'indexes' refers to a CompositePrimaryKey 'pk', but "
                    "CompositePrimaryKeys are not permitted in 'indexes'.",
                    obj=Model,
                    id="models.E048",
                ),
            ],
        )