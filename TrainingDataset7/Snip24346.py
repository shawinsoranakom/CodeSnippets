def test_linearring_json(self):
        self.assertJSONEqual(
            LinearRing((0, 0), (0, 1), (1, 1), (0, 0)).json,
            '{"coordinates": [[0, 0], [0, 1], [1, 1], [0, 0]], "type": "LineString"}',
        )