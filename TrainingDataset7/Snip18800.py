def test_callproc_without_params(self):
        self._test_procedure(
            connection.features.create_test_procedure_without_params_sql, [], []
        )