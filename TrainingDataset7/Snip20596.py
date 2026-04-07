def test_equal(self):
        self.assertEqual(
            Concat("foo", "bar", output_field=TextField()),
            Concat("foo", "bar", output_field=TextField()),
        )
        self.assertNotEqual(
            Concat("foo", "bar", output_field=TextField()),
            Concat("foo", "bar", output_field=CharField()),
        )
        self.assertNotEqual(
            Concat("foo", "bar", output_field=TextField()),
            Concat("bar", "foo", output_field=TextField()),
        )