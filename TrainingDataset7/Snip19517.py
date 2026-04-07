def test_not_equal_to_non_check(self):
        e = Error("Error", obj=DummyObj())
        self.assertNotEqual(e, "a string")