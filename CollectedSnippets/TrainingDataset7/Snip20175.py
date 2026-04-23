def test_lookup_on_transform(self):
        transform = Div3Transform
        with register_lookup(Div3Transform, CustomStartsWith):
            with register_lookup(Div3Transform, CustomEndsWith):
                self.assertEqual(
                    transform.get_lookups(),
                    {"sw": CustomStartsWith, "ew": CustomEndsWith},
                )
            self.assertEqual(transform.get_lookups(), {"sw": CustomStartsWith})
        self.assertEqual(transform.get_lookups(), {})