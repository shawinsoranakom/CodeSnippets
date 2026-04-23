def test_callproc_with_int_params(self):
        self._test_procedure(
            connection.features.create_test_procedure_with_int_param_sql,
            [1],
            ["INTEGER"],
        )