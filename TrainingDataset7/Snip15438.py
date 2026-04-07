def test_listfilter_without_title(self):
        """
        Any filter must define a title.
        """
        modeladmin = DecadeFilterBookAdminWithoutTitle(Book, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        msg = (
            "The list filter 'DecadeListFilterWithoutTitle' does not specify a 'title'."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            modeladmin.get_changelist_instance(request)