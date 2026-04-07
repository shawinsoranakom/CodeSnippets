def test_must_update(self):
        self.assertIs(self.hasher.must_update("encoded"), False)