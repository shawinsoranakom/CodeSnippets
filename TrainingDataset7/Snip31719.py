def test_helpful_error_message_for_many2many_natural1(self):
        """
        Invalid many-to-many keys throws a helpful error message where one of a
        list of natural keys is invalid.
        """
        test_strings = [
            """{
                "pk": 1,
                "model": "serializers.categorymetadata",
                "fields": {"kind": "author","name": "meta1","value": "Agnes"}
            }""",
            """{
                "pk": 1,
                "model": "serializers.article",
                "fields": {
                    "author": 1,
                    "headline": "Unknown many to many",
                    "pub_date": "2014-09-15T10:35:00",
                    "meta_data": [
                        ["author", "meta1"],
                        ["doesnotexist", "meta1"],
                        ["author", "meta1"]
                    ]
                }
            }""",
            """{
                "pk": 1,
                "model": "serializers.author",
                "fields": {"name": "Agnes"}
            }""",
        ]
        test_string = "\n".join([s.replace("\n", "") for s in test_strings])
        key = ["doesnotexist", "meta1"]
        expected = "(serializers.article:pk=1) field_value was '%r'" % key
        with self.assertRaisesMessage(DeserializationError, expected):
            for obj in serializers.deserialize("jsonl", test_string):
                obj.save()