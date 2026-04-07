def test_related_name(self):
        """
        Regression test for #13963
        """
        self.assertEqual(
            label_for_field("location", Event, return_attr=True),
            ("location", None),
        )
        self.assertEqual(
            label_for_field("event", Location, return_attr=True),
            ("awesome event", None),
        )
        self.assertEqual(
            label_for_field("guest", Event, return_attr=True),
            ("awesome guest", None),
        )