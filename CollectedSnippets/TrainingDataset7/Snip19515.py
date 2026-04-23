def test_equal_to_same_constructed_check(self):
        e1 = Error("Error", obj=SimpleModel)
        e2 = Error("Error", obj=SimpleModel)
        self.assertEqual(e1, e2)