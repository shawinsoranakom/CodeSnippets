def test_exact_query_rhs_with_selected_columns_mismatch(self):
        msg = (
            "The QuerySet value for the exact lookup must have 1 "
            "selected fields (received 2)"
        )
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.filter(id=Author.objects.values("id", "name")[:1])