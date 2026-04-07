def test_simplelistfilter_without_parameter(self):
        """
        Any SimpleListFilter must define a parameter_name.
        """
        modeladmin = DecadeFilterBookAdminWithoutParameter(Book, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        msg = (
            "The list filter 'DecadeListFilterWithoutParameter' does not specify a "
            "'parameter_name'."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            modeladmin.get_changelist_instance(request)