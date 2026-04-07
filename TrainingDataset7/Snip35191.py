def test_repr(self):
        self.assertEqual(
            repr(TestData("attr", "value")),
            "<TestData: name='attr', data='value'>",
        )