def test_json_encoder_decoder(self):
        """
        A complex nested data structure containing Message
        instances is properly encoded/decoded by the custom JSON
        encoder/decoder classes.
        """
        messages = [
            {
                "message": Message(constants.INFO, "Test message"),
                "message_list": [
                    Message(constants.INFO, "message %s") for x in range(5)
                ]
                + [{"another-message": Message(constants.ERROR, "error")}],
            },
            Message(constants.INFO, "message %s"),
        ]
        encoder = MessageEncoder()
        value = encoder.encode(messages)
        decoded_messages = json.loads(value, cls=MessageDecoder)
        self.assertEqual(messages, decoded_messages)