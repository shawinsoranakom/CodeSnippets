def test_filter_non_conditional(self):
        query = Query(Item)
        msg = "Cannot filter against a non-conditional expression."
        with self.assertRaisesMessage(TypeError, msg):
            query.build_where(Func(output_field=CharField()))