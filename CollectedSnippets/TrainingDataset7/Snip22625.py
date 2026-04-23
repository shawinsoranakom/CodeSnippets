def test_has_changed(self):
        field = JSONField()
        self.assertIs(field.has_changed({"a": True}, '{"a": 1}'), True)
        self.assertIs(field.has_changed({"a": 1, "b": 2}, '{"b": 2, "a": 1}'), False)