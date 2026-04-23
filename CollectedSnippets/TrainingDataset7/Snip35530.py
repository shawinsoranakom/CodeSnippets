def test_change_editable_in_other_timezone(self):
        e = Event.objects.create(
            dt=datetime.datetime(2011, 9, 1, 10, 20, 30, tzinfo=UTC)
        )
        with timezone.override(ICT):
            response = self.client.get(
                reverse("admin_tz:timezones_event_change", args=(e.pk,))
            )
        self.assertContains(response, e.dt.astimezone(ICT).date().isoformat())
        self.assertContains(response, e.dt.astimezone(ICT).time().isoformat())