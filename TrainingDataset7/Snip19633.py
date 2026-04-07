def test_unsupported_rhs(self):
        pk = Exact(F("tenant_id"), 1)
        msg = (
            "'exact' subquery lookup of 'pk' only supports OuterRef "
            "and QuerySet objects (received 'Exact')"
        )
        with self.assertRaisesMessage(ValueError, msg):
            Comment.objects.filter(pk=pk)