def test_no_distinct_for_m2m_in_list_filter_without_params(self):
        """
        If a ManyToManyField is in list_filter but isn't in any lookup params,
        the changelist's query shouldn't have distinct.
        """
        m = BandAdmin(Band, custom_site)
        for lookup_params in ({}, {"name": "test"}):
            request = self.factory.get("/band/", lookup_params)
            request.user = self.superuser
            cl = m.get_changelist_instance(request)
            self.assertIs(cl.queryset.query.distinct, False)

        # A ManyToManyField in params does have distinct applied.
        request = self.factory.get("/band/", {"genres": "0"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertIs(cl.queryset.query.distinct, True)