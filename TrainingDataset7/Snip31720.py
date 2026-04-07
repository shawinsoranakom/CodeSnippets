def test_helpful_error_message_for_many2many_natural2(self):
        """
        Invalid many-to-many keys throws a helpful error message where a
        natural many-to-many key has only a single value.
        """
        test_strings = [
            """{
                "pk": 1,
                "model": "serializers.article",
                "fields": {
                    "author": 1,
                    "headline": "Unknown many to many",
                    "pub_date": "2014-09-15T10:35:00",
                    "meta_data": [1, "doesnotexist"]
                }
            }""",
            """{
                "pk": 1,
                "model": "serializers.categorymetadata",
                "fields": {"kind": "author","name": "meta1","value": "Agnes"}
            }""",
            """{
                "pk": 1,
                "model": "serializers.author",
                "fields": {"name": "Agnes"}
            }""",
        ]
        test_string = "\n".join([s.replace("\n", "") for s in test_strings])
        expected = "(serializers.article:pk=1) field_value was 'doesnotexist'"
        with self.assertRaisesMessage(DeserializationError, expected):
            for obj in serializers.deserialize("jsonl", test_string, ignore=False):
                obj.save()