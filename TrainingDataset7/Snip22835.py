def test_label_split_datetime_not_displayed(self):
        class EventForm(Form):
            happened_at = SplitDateTimeField(widget=SplitHiddenDateTimeWidget)

        form = EventForm()
        self.assertHTMLEqual(
            form.as_ul(),
            '<input type="hidden" name="happened_at_0" id="id_happened_at_0">'
            '<input type="hidden" name="happened_at_1" id="id_happened_at_1">',
        )