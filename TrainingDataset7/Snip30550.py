def test_filter_conditional_join(self):
        query = Query(Item)
        filter_expr = Func("note__note", output_field=BooleanField())
        msg = "Joined field references are not permitted in this query"
        with self.assertRaisesMessage(FieldError, msg):
            query.build_where(filter_expr)