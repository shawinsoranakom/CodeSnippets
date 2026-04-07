def test_fromkeys_is_immutable_by_default(self):
        # Match behavior of __init__() which is also immutable by default.
        q = QueryDict.fromkeys(["key1", "key2", "key3"])
        with self.assertRaisesMessage(
            AttributeError, "This QueryDict instance is immutable"
        ):
            q["key4"] = "nope"