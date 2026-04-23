def test_helpful_error_message_for_many2many_non_natural(self):
        """
        Invalid many-to-many keys throws a helpful error message.
        """
        test_strings = [
            """{
                "pk": 1,
                "model": "serializers.article",
                "fields": {
                    "author": 1,
                    "headline": "Unknown many to many",
                    "pub_date": "2014-09-15T10:35:00",
                    "categories": [1, "doesnotexist"]
                }
            }""",
            """{
                "pk": 1,
                "model": "serializers.author",
                "fields": {"name": "Agnes"}
            }""",
            """{
                "pk": 1,
                "model": "serializers.category",
                "fields": {"name": "Reference"}
            }""",
        ]
        test_string = "\n".join([s.replace("\n", "") for s in test_strings])
        expected = "(serializers.article:pk=1) field_value was 'doesnotexist'"
        with self.assertRaisesMessage(DeserializationError, expected):
            list(serializers.deserialize("jsonl", test_string))