def test_request_signals_streaming_response(self):
        response = self.client.get("/streaming/")
        self.assertEqual(self.signals, ["started"])
        self.assertEqual(b"".join(list(response)), b"streaming content")
        self.assertEqual(self.signals, ["started", "finished"])