def test_value_from_datadict_string_int(self):
        value = self.widget.value_from_datadict({"testing": "0"}, {}, "testing")
        self.assertIs(value, True)