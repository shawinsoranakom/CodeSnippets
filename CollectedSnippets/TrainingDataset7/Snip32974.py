def test_without_id(self):
        output = self.engine.render_to_string("json-tag02", {"value": {}})
        self.assertEqual(output, '<script type="application/json">{}</script>')