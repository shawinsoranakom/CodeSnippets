def test_template_source_warning(self):
        partial = engine.get_template("partial_examples.html#test-partial")
        with self.assertWarnsMessage(
            RuntimeWarning,
            "PartialTemplate.source is only available when template "
            "debugging is enabled.",
        ) as ctx:
            self.assertEqual(partial.template.source, "")
        self.assertEqual(ctx.filename, __file__)