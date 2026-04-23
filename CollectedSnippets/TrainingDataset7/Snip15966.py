def test_label_for_property(self):
        class MockModelAdmin:
            @property
            @admin.display(description="property short description")
            def test_from_property(self):
                return "this if from property"

        self.assertEqual(
            label_for_field("test_from_property", Article, model_admin=MockModelAdmin),
            "property short description",
        )