def test_redisplay_none_input(self):
        class JSONForm(Form):
            json_field = JSONField(required=True)

        tests = [
            {},
            {"json_field": None},
        ]
        for data in tests:
            with self.subTest(data=data):
                form = JSONForm(data)
                self.assertEqual(form["json_field"].value(), "null")
                self.assertIn("null</textarea>", form.as_p())
                self.assertEqual(form.errors["json_field"], ["This field is required."])