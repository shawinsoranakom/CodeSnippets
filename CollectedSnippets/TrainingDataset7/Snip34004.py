def test_url04(self):
        output = self.engine.render_to_string("url04", {"client": {"id": 1}})
        self.assertEqual(output, "/named-client/1/")