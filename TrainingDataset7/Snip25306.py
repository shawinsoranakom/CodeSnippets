def test_pointing_to_composite_primary_key(self):
        class Model(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

            class Meta:
                unique_together = [["pk"]]

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "'unique_together' refers to a CompositePrimaryKey 'pk', but "
                    "CompositePrimaryKeys are not permitted in 'unique_together'.",
                    obj=Model,
                    id="models.E048",
                ),
            ],
        )