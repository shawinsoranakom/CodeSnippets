def test_valid_transaction_modes(self):
        valid_transaction_modes = ("deferred", "immediate", "exclusive")
        for transaction_mode in valid_transaction_modes:
            with (
                self.subTest(transaction_mode=transaction_mode),
                self.change_transaction_mode(transaction_mode) as new_connection,
                CaptureQueriesContext(new_connection) as captured_queries,
            ):
                new_connection.set_autocommit(
                    False, force_begin_transaction_with_broken_autocommit=True
                )
                new_connection.commit()
                expected_transaction_mode = transaction_mode.upper()
                begin_sql = captured_queries[0]["sql"]
                self.assertEqual(begin_sql, f"BEGIN {expected_transaction_mode}")