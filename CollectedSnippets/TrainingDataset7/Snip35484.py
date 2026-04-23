def test_update_with_timedelta(self):
        initial_dt = timezone.now().replace(microsecond=0)
        event = Event.objects.create(dt=initial_dt)
        Event.objects.update(dt=F("dt") + timedelta(hours=2))
        event.refresh_from_db()
        self.assertEqual(event.dt, initial_dt + timedelta(hours=2))