def test_url12(self):
        output = self.engine.render_to_string("url12", {"client": {"id": 1}})
        self.assertEqual(output, "/client/1/!$&amp;&#x27;()*+,;=~:@,/")