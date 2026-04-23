def test_output_transaction(self):
        output = management.call_command(
            "transaction", stdout=StringIO(), no_color=True
        )
        self.assertTrue(
            output.strip().startswith(connection.ops.start_transaction_sql())
        )
        self.assertTrue(output.strip().endswith(connection.ops.end_transaction_sql()))