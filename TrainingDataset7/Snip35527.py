def test_changelist(self):
        e = Event.objects.create(
            dt=datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        )
        response = self.client.get(reverse("admin_tz:timezones_event_changelist"))
        self.assertContains(response, e.dt.astimezone(EAT).isoformat())