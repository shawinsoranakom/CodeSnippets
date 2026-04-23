def test_end_transaction_rollback(self):
        self.assertEqual(self.ops.end_transaction_sql(success=False), "ROLLBACK;")