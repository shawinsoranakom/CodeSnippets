def test_unregister(self):
        """
        Unregistering a serializer doesn't cause the registry to be
        repopulated.
        """
        serializers.unregister_serializer("xml")
        serializers.register_serializer("json3", "django.core.serializers.json")

        public_formats = serializers.get_public_serializer_formats()

        self.assertNotIn("xml", public_formats)
        self.assertIn("json3", public_formats)