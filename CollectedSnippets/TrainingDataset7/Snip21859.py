def _test_file_time_getter_tz_handling_off(self, getter):
        # Django's TZ (and hence the system TZ) is set to Africa/Algiers which
        # is UTC+1 and has no DST change. We can set the Django TZ to something
        # else so that UTC, Django's TIME_ZONE, and the system timezone are all
        # different.
        now_in_algiers = timezone.make_aware(datetime.datetime.now())

        with timezone.override(timezone.get_fixed_timezone(-300)):
            # At this point the system TZ is +1 and the Django TZ
            # is -5.
            self.assertFalse(self.storage.exists("test.file.tz.off"))

            f = ContentFile("custom contents")
            f_name = self.storage.save("test.file.tz.off", f)
            self.addCleanup(self.storage.delete, f_name)
            dt = getter(f_name)
            # dt should be naive, in system (+1) TZ
            self.assertTrue(timezone.is_naive(dt))

            # The three timezones are indeed distinct.
            naive_now = datetime.datetime.now()
            algiers_offset = now_in_algiers.tzinfo.utcoffset(naive_now)
            django_offset = timezone.get_current_timezone().utcoffset(naive_now)
            utc_offset = datetime.UTC.utcoffset(naive_now)
            self.assertGreater(algiers_offset, utc_offset)
            self.assertLess(django_offset, utc_offset)

            # dt and naive_now should be the same effective time.
            self.assertLess(abs(dt - naive_now), datetime.timedelta(seconds=2))
            # If we convert dt to an aware object using the Algiers
            # timezone then it should be the same effective time to
            # now_in_algiers.
            _dt = timezone.make_aware(dt, now_in_algiers.tzinfo)
            self.assertLess(abs(_dt - now_in_algiers), datetime.timedelta(seconds=2))