def test_name_constraints(self):
        class Model(models.Model):
            class Meta:
                indexes = [
                    models.Index(fields=["id"], name="_index_name"),
                    models.Index(fields=["id"], name="5index_name"),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "The index name '%sindex_name' cannot start with an "
                    "underscore or a number." % prefix,
                    obj=Model,
                    id="models.E033",
                )
                for prefix in ("_", "5")
            ],
        )