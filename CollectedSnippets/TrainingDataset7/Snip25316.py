def test_max_name_length(self):
        index_name = "x" * 31

        class Model(models.Model):
            class Meta:
                indexes = [models.Index(fields=["id"], name=index_name)]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "The index name '%s' cannot be longer than 30 characters."
                    % index_name,
                    obj=Model,
                    id="models.E034",
                ),
            ],
        )