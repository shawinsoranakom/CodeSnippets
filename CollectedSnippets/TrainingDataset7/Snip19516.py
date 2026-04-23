def test_not_equal_to_different_constructed_check(self):
        e1 = Error("Error", obj=SimpleModel)
        e2 = Error("Error2", obj=SimpleModel)
        self.assertNotEqual(e1, e2)