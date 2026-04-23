def test_durationfield_render(self):
        self.assertWidgetRendersTo(
            DurationField(initial=datetime.timedelta(hours=1)),
            '<input id="id_f" type="text" name="f" value="01:00:00" required>',
        )