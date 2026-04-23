def test_helpful_error_message_invalid_field(self):
        """
        If there is an invalid field value, the error message contains the
        model associated with it.
        """
        test_string = (
            '{"pk": "1","model": "serializers.player",'
            '"fields": {"name": "Bob","rank": "invalidint","team": "Team"}}'
        )
        expected = "(serializers.player:pk=1) field_value was 'invalidint'"
        with self.assertRaisesMessage(DeserializationError, expected):
            list(serializers.deserialize("jsonl", test_string))