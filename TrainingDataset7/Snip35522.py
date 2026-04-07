def test_localized_form(self):
        form = EventLocalizedForm(
            initial={"dt": datetime.datetime(2011, 9, 1, 13, 20, 30, tzinfo=EAT)}
        )
        with timezone.override(ICT):
            self.assertIn("2011-09-01 17:20:30", str(form))