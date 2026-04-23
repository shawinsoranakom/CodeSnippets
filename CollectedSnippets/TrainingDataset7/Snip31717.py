def test_helpful_error_message_for_foreign_keys(self):
        """
        Invalid foreign keys with a natural key throws a helpful error message,
        such as what the failing key is.
        """
        test_string = (
            '{"pk": 1, "model": "serializers.category",'
            '"fields": {'
            '"name": "Unknown foreign key",'
            '"meta_data": ["doesnotexist","metadata"]}}'
        )
        key = ["doesnotexist", "metadata"]
        expected = "(serializers.category:pk=1) field_value was '%r'" % key
        with self.assertRaisesMessage(DeserializationError, expected):
            list(serializers.deserialize("jsonl", test_string))