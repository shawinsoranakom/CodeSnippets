def test_builtin_serializers(self):
        """
        'geojson' should be listed in available serializers.
        """
        all_formats = set(serializers.get_serializer_formats())
        public_formats = set(serializers.get_public_serializer_formats())

        self.assertIn("geojson", all_formats)
        self.assertIn("geojson", public_formats)