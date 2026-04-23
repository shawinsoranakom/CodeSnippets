def test_helpful_error_message_invalid_pk(self):
        """
        If there is an invalid primary key, the error message contains the
        model associated with it.
        """
        test_string = (
            '{"pk": "badpk","model": "serializers.player",'
            '"fields": {"name": "Bob","rank": 1,"team": "Team"}}'
        )
        with self.assertRaisesMessage(
            DeserializationError, "(serializers.player:pk=badpk)"
        ):
            list(serializers.deserialize("jsonl", test_string))