def test_helpful_error_message_for_many2many_not_iterable(self):
        """
        Not iterable many-to-many field value throws a helpful error message.
        """
        test_string = """[{
            "pk": 1,
            "model": "serializers.m2mdata",
            "fields": {"data": null}
        }]"""

        expected = "(serializers.m2mdata:pk=1) field_value was 'None'"
        with self.assertRaisesMessage(DeserializationError, expected):
            next(serializers.deserialize("json", test_string, ignore=False))