def test_message_dict(self):
        v = ValidationError({"first": ["First Problem"]})
        self.assertEqual(str(v), "{'first': ['First Problem']}")
        self.assertEqual(repr(v), "ValidationError({'first': ['First Problem']})")