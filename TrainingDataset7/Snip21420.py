def test_contains(self):
        msg = "argument of type 'F' is not iterable"
        with self.assertRaisesMessage(TypeError, msg):
            "" in F("name")