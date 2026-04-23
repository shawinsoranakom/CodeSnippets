def test_origin_from_string(self):
        template = self.engine.from_string("Hello!\n")
        self.assertEqual(template.origin.name, "<template>")
        self.assertIsNone(template.origin.template_name)