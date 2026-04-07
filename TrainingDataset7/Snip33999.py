def test_url02(self):
        output = self.engine.render_to_string("url02", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/update/")