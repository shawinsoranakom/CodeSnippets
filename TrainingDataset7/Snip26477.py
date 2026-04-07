def test_message_rfc6265(self):
        non_compliant_chars = ["\\", ",", ";", '"']
        messages = ["\\te,st", ';m"e', "\u2019", '123"NOTRECEIVED"']
        storage = self.get_storage()
        encoded = storage._encode(messages)
        for illegal in non_compliant_chars:
            self.assertEqual(encoded.find(illegal), -1)