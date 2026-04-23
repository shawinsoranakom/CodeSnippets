def test_indexes(self):
        class IndexModel(PostgreSQLModel):
            field = models.IntegerField()

            class Meta:
                indexes = [
                    PostgresIndex(fields=["id"], name="postgres_index_test"),
                    GinIndex(fields=["field"], name="gin_index_test"),
                ]

        self.assert_model_check_errors(
            IndexModel,
            [
                self._make_error(IndexModel, "PostgresIndex"),
                self._make_error(IndexModel, "GinIndex"),
            ],
        )