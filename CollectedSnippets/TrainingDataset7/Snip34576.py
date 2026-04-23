def test_json_encoder_argument(self):
        """The test Client accepts a json_encoder."""
        mock_encoder = mock.MagicMock()
        mock_encoding = mock.MagicMock()
        mock_encoder.return_value = mock_encoding
        mock_encoding.encode.return_value = '{"value": 37}'

        client = self.client_class(json_encoder=mock_encoder)
        # Vendored tree JSON content types are accepted.
        client.post(
            "/json_view/", {"value": 37}, content_type="application/vnd.api+json"
        )
        self.assertTrue(mock_encoder.called)
        self.assertTrue(mock_encoding.encode.called)