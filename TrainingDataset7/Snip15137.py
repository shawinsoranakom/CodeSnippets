def test_changelist_search_form_validation(self):
        m = ConcertAdmin(Concert, custom_site)
        tests = [
            ({SEARCH_VAR: "\x00"}, "Null characters are not allowed."),
            ({SEARCH_VAR: "some\x00thing"}, "Null characters are not allowed."),
        ]
        for case, error in tests:
            with self.subTest(case=case):
                request = self.factory.get("/concert/", case)
                request.user = self.superuser
                request._messages = CookieStorage(request)
                m.get_changelist_instance(request)
                messages = [m.message for m in request._messages]
                self.assertEqual(1, len(messages))
                self.assertEqual(error, messages[0])