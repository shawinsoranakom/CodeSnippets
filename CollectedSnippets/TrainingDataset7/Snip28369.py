def test_notrequired_overrides_notblank(self):
        form = CustomWriterForm({})
        self.assertIs(form.is_valid(), True)