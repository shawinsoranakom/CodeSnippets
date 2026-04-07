def test_equal_to_self(self):
        e = Error("Error", obj=SimpleModel)
        self.assertEqual(e, e)