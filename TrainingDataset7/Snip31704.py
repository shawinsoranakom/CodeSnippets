def test_helpful_error_message_for_many2many_natural2(self):
        """
        Invalid many-to-many keys should throw a helpful error message. This
        tests the code path where a natural many-to-many key has only a single
        value.
        """
        test_string = """[{
            "pk": 1,
            "model": "serializers.article",
            "fields": {
                "author": 1,
                "headline": "Unknown many to many",
                "pub_date": "2014-09-15T10:35:00",
                "meta_data": [1, "doesnotexist"]
            }
        }, {
            "pk": 1,
            "model": "serializers.categorymetadata",
            "fields": {
                "kind": "author",
                "name": "meta1",
                "value": "Agnes"
            }
        }, {
            "pk": 1,
            "model": "serializers.author",
            "fields": {
                "name": "Agnes"
            }
        }]"""
        expected = "(serializers.article:pk=1) field_value was 'doesnotexist'"
        with self.assertRaisesMessage(DeserializationError, expected):
            for obj in serializers.deserialize("json", test_string, ignore=False):
                obj.save()