def test_render_no_disabled(self):
        class TestForm(Form):
            clearable_file = FileField(
                widget=self.widget, initial=FakeFieldFile(), required=False
            )

        form = TestForm()
        with self.assertNoLogs("django.template", "DEBUG"):
            form.render()