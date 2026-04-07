def test_url02c(self):
        output = self.engine.render_to_string("url02c", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/update/")