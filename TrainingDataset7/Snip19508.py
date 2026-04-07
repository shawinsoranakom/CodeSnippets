def test_printing_no_hint(self):
        e = Error("Message", obj=DummyObj())
        expected = "obj: Message"
        self.assertEqual(str(e), expected)