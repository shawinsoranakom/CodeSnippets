def test_emptylistfieldfilter_non_empty_field(self):
        class EmployeeAdminWithEmptyFieldListFilter(ModelAdmin):
            list_filter = [("department", EmptyFieldListFilter)]

        modeladmin = EmployeeAdminWithEmptyFieldListFilter(Employee, site)
        request = self.request_factory.get("/")
        request.user = self.alfred
        msg = (
            "The list filter 'EmptyFieldListFilter' cannot be used with field "
            "'department' which doesn't allow empty strings and nulls."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            modeladmin.get_changelist_instance(request)