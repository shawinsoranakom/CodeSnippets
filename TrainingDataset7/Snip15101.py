def assertDateParams(self, query, expected_from_date, expected_to_date):
        query = {"date__%s" % field: val for field, val in query.items()}
        request = self.factory.get("/", query)
        request.user = self.superuser
        changelist = EventAdmin(Event, custom_site).get_changelist_instance(request)
        _, _, lookup_params, *_ = changelist.get_filters(request)
        self.assertEqual(lookup_params["date__gte"], [expected_from_date])
        self.assertEqual(lookup_params["date__lt"], [expected_to_date])