def test_validate_constraints_success_case_single_query(self):
        customer_tab = CustomerTab(customer_id=500)
        with CaptureQueriesContext(connection) as ctx:
            customer_tab.validate_constraints()
        select_queries = [
            query["sql"]
            for query in ctx.captured_queries
            if "select" in query["sql"].lower()
        ]
        self.assertEqual(len(select_queries), 1)