def test_unsupported_callproc_kparams_raises_error(self):
        msg = (
            "Keyword parameters for callproc are not supported on this database "
            "backend."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            with connection.cursor() as cursor:
                cursor.callproc("test_procedure", [], {"P_I": 1})