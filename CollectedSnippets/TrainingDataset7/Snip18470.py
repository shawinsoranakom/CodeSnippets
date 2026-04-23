def test_wrapper_debug(self):
        def wrap_with_comment(execute, sql, params, many, context):
            return execute(f"/* My comment */ {sql}", params, many, context)

        with CaptureQueriesContext(connection) as ctx:
            with connection.execute_wrapper(wrap_with_comment):
                list(Person.objects.all())
        last_query = ctx.captured_queries[-1]["sql"]
        self.assertTrue(last_query.startswith("/* My comment */"))