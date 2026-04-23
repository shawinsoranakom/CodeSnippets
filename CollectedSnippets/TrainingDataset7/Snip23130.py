def test_merge_warning(self):
        msg = "Detected duplicate Media files in an opposite order: [1, 2], [2, 1]"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            self.assertEqual(Media.merge([1, 2], [2, 1], None), [1, 2])