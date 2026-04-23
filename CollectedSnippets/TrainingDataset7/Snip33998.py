def test_url01(self):
        output = self.engine.render_to_string("url01", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/")