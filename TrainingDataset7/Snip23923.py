def test_update_or_create_with_model_property_defaults(self):
        """Using a property with a setter implemented is allowed."""
        t, _ = Thing.objects.update_or_create(
            defaults={"capitalized_name_property": "annie"}, pk=1
        )
        self.assertEqual(t.name, "Annie")