def test_full_template_from_loader(self):
        template = engine.get_template("partial_examples.html")
        rendered = template.render({})

        # Check the partial was rendered twice
        self.assertEqual(2, rendered.count("TEST-PARTIAL-CONTENT"))
        self.assertEqual(1, rendered.count("INLINE-CONTENT"))