def test_extract_duration_unsupported_lookups(self):
        msg = "Cannot extract component '%s' from DurationField 'duration'."
        for lookup in (
            "year",
            "iso_year",
            "month",
            "week",
            "week_day",
            "iso_week_day",
            "quarter",
        ):
            with self.subTest(lookup):
                with self.assertRaisesMessage(ValueError, msg % lookup):
                    DTModel.objects.annotate(extracted=Extract("duration", lookup))