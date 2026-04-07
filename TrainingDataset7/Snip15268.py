def test_list_filter_works_on_through_field_even_when_apps_not_ready(self):
        """
        Ensure list_filter can access reverse fields even when the app registry
        is not ready; refs #24146.
        """

        class BookAdminWithListFilter(admin.ModelAdmin):
            list_filter = ["authorsbooks__featured"]

        # Temporarily pretending apps are not ready yet. This issue can happen
        # if the value of 'list_filter' refers to a 'through__field'.
        Book._meta.apps.ready = False
        try:
            errors = BookAdminWithListFilter(Book, AdminSite()).check()
            self.assertEqual(errors, [])
        finally:
            Book._meta.apps.ready = True