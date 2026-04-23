def test_list_filter_queryset_filtered_by_default(self):
        """
        A list filter that filters the queryset by default gives the correct
        full_result_count.
        """
        modeladmin = NotNinetiesListFilterAdmin(Book, site)
        request = self.request_factory.get("/", {})
        request.user = self.alfred
        changelist = modeladmin.get_changelist_instance(request)
        changelist.get_results(request)
        self.assertEqual(changelist.full_result_count, 4)