def test_serialize_compiled_regex(self):
        """
        Make sure compiled regex can be serialized.
        """
        regex = re.compile(r"^\w+$")
        self.assertSerializedEqual(regex)