def test_filter_with_failing_queryset(self):
        """
        When a filter's queryset method fails, it fails loudly and
        the corresponding exception doesn't get swallowed (#17828).
        """
        modeladmin = DecadeFilterBookAdminWithFailingQueryset(Book, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        with self.assertRaises(ZeroDivisionError):
            modeladmin.get_changelist_instance(request)