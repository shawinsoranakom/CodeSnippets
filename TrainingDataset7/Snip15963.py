def test_label_for_field(self):
        """
        Tests for label_for_field
        """
        self.assertEqual(label_for_field("title", Article), "title")
        self.assertEqual(label_for_field("hist", Article), "History")
        self.assertEqual(
            label_for_field("hist", Article, return_attr=True), ("History", None)
        )

        self.assertEqual(label_for_field("__str__", Article), "article")

        with self.assertRaisesMessage(
            AttributeError, "Unable to lookup 'unknown' on Article"
        ):
            label_for_field("unknown", Article)

        def test_callable(obj):
            return "nothing"

        self.assertEqual(label_for_field(test_callable, Article), "Test callable")
        self.assertEqual(
            label_for_field(test_callable, Article, return_attr=True),
            ("Test callable", test_callable),
        )

        self.assertEqual(label_for_field("test_from_model", Article), "Test from model")
        self.assertEqual(
            label_for_field("test_from_model", Article, return_attr=True),
            ("Test from model", Article.test_from_model),
        )
        self.assertEqual(
            label_for_field("test_from_model_with_override", Article),
            "not What you Expect",
        )

        self.assertEqual(label_for_field(lambda x: "nothing", Article), "--")
        self.assertEqual(label_for_field("site_id", Article), "Site id")
        # The correct name and attr are returned when `__` is in the field
        # name.
        self.assertEqual(label_for_field("site__domain", Article), "Site  domain")
        self.assertEqual(
            label_for_field("site__domain", Article, return_attr=True),
            ("Site  domain", Site._meta.get_field("domain")),
        )