def test_filter_by_pk_in_subquery_invalid_selected_columns(self):
        msg = (
            "The QuerySet value for the 'in' lookup must have 2 selected "
            "fields (received 3)"
        )
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(pk__in=Comment.objects.values("pk", "text"))