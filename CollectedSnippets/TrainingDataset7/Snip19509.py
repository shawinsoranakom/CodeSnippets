def test_printing_no_object(self):
        e = Error("Message", hint="Hint")
        expected = "?: Message\n\tHINT: Hint"
        self.assertEqual(str(e), expected)