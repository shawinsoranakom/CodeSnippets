def test_printing_with_given_id(self):
        e = Error("Message", hint="Hint", obj=DummyObj(), id="ID")
        expected = "obj: (ID) Message\n\tHINT: Hint"
        self.assertEqual(str(e), expected)