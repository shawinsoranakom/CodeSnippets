def test_url02b(self):
        output = self.engine.render_to_string("url02b", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/update/")