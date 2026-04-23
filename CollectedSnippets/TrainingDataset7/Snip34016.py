def test_url19(self):
        output = self.engine.render_to_string(
            "url19", {"client": {"id": 1}, "named_url": "client"}
        )
        self.assertEqual(output, "/client/1/")