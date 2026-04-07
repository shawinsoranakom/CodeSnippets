def test_uuidfield_2(self):
        field = UUIDField(required=False)
        self.assertIsNone(field.clean(""))
        self.assertIsNone(field.clean(None))