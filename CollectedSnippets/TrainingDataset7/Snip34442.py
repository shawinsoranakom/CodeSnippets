def test_partial_engine_assignment_with_real_template(self):
        template_with_partial = engine.get_template(
            "partial_examples.html#test-partial"
        )
        self.assertEqual(template_with_partial.template.engine, engine.engine)
        rendered_content = template_with_partial.render({})
        self.assertEqual("TEST-PARTIAL-CONTENT", rendered_content.strip())