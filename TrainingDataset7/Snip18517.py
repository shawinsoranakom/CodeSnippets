def test_sql_flush(self):
        msg = "subclasses of BaseDatabaseOperations must provide an sql_flush() method"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.ops.sql_flush(None, None)