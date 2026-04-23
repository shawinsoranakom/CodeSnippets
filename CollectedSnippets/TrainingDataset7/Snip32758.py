def test_from_string(self):
        template = self.engine.from_string("Hello!\n")
        content = template.render()
        self.assertEqual(content, "Hello!\n")