def test_printing(self):
        e = Error("Message", hint="Hint", obj=DummyObj())
        expected = "obj: Message\n\tHINT: Hint"
        self.assertEqual(str(e), expected)