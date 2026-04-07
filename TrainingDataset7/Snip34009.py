def test_url10(self):
        output = self.engine.render_to_string("url10", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/two%20words/")