def test_computed_list_display_localization(self):
        """
        Regression test for #13196: output of functions should be  localized
        in the changelist.
        """
        self.client.force_login(self.superuser)
        event = Event.objects.create(date=datetime.date.today())
        response = self.client.get(reverse("admin:admin_changelist_event_changelist"))
        self.assertContains(response, formats.localize(event.date))
        self.assertNotContains(response, str(event.date))