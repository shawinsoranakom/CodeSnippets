def test_invalid_string(self):
        field = models.DurationField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("not a datetime", None)
        self.assertEqual(cm.exception.code, "invalid")
        self.assertEqual(
            cm.exception.message % cm.exception.params,
            "“not a datetime” value has an invalid format. "
            "It must be in [DD] [[HH:]MM:]ss[.uuuuuu] format.",
        )