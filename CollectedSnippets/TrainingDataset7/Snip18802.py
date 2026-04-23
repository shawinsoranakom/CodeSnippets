def test_callproc_kparams(self):
        self._test_procedure(
            connection.features.create_test_procedure_with_int_param_sql,
            [],
            ["INTEGER"],
            {"P_I": 1},
        )