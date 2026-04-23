def test_label_for_field_failed_lookup(self):
        msg = "Unable to lookup 'site__unknown' on Article"
        with self.assertRaisesMessage(AttributeError, msg):
            label_for_field("site__unknown", Article)

        class MockModelAdmin:
            @admin.display(description="not Really the Model")
            def test_from_model(self, obj):
                return "nothing"

        self.assertEqual(
            label_for_field("test_from_model", Article, model_admin=MockModelAdmin),
            "not Really the Model",
        )
        self.assertEqual(
            label_for_field(
                "test_from_model", Article, model_admin=MockModelAdmin, return_attr=True
            ),
            ("not Really the Model", MockModelAdmin.test_from_model),
        )