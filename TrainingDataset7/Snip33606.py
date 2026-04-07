def test_filter03(self):
        output = self.engine.render_to_string("filter03")
        self.assertEqual(output, "django")