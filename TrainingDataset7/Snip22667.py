def test_regexfield_unicode_characters(self):
        f = RegexField(r"^\w+$")
        self.assertEqual("éèøçÎÎ你好", f.clean("éèøçÎÎ你好"))