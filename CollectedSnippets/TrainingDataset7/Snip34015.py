def test_url18(self):
        output = self.engine.render_to_string("url18")
        self.assertEqual(output, "/client/1,2/")