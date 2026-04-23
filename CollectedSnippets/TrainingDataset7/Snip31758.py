def test_builtin_serializers(self):
        "Requesting a list of serializer formats populates the registry"
        all_formats = set(serializers.get_serializer_formats())
        public_formats = set(serializers.get_public_serializer_formats())

        self.assertIn("xml", all_formats)
        self.assertIn("xml", public_formats)

        self.assertIn("json2", all_formats)
        self.assertIn("json2", public_formats)

        self.assertIn("python", all_formats)
        self.assertNotIn("python", public_formats)