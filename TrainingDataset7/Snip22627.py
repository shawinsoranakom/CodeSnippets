def test_formfield_disabled(self):
        class JSONForm(Form):
            json_field = JSONField(disabled=True)

        form = JSONForm({"json_field": '["bar"]'}, initial={"json_field": ["foo"]})
        self.assertIn("[&quot;foo&quot;]</textarea>", form.as_p())