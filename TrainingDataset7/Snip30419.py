def test_multi_page_text_explain(self):
        if "TEXT" not in connection.features.supported_explain_formats:
            self.skipTest("This backend does not support TEXT format.")

        base_qs = Tag.objects.order_by()
        qs = base_qs.filter(name="test").union(*[base_qs for _ in range(100)])
        result = qs.explain(format="text")
        self.assertGreaterEqual(result.count("\n"), 100)