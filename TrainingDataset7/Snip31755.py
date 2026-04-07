def test_register(self):
        "Registering a new serializer populates the full registry. Refs #14823"
        serializers.register_serializer("json3", "django.core.serializers.json")

        public_formats = serializers.get_public_serializer_formats()
        self.assertIn("json3", public_formats)
        self.assertIn("json2", public_formats)
        self.assertIn("xml", public_formats)