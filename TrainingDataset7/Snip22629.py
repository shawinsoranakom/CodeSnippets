def test_redisplay_wrong_input(self):
        """
        Displaying a bound form (typically due to invalid input). The form
        should not overquote JSONField inputs.
        """

        class JSONForm(Form):
            name = CharField(max_length=2)
            json_field = JSONField()

        # JSONField input is valid, name is too long.
        form = JSONForm({"name": "xyz", "json_field": '["foo"]'})
        self.assertNotIn("json_field", form.errors)
        self.assertIn("[&quot;foo&quot;]</textarea>", form.as_p())
        # Invalid JSONField.
        form = JSONForm({"name": "xy", "json_field": '{"foo"}'})
        self.assertEqual(form.errors["json_field"], ["Enter a valid JSON."])
        self.assertIn("{&quot;foo&quot;}</textarea>", form.as_p())