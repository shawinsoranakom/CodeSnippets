def test_error_dict_html_safe(self):
        e = ErrorDict()
        e["username"] = "Invalid username."
        self.assertTrue(hasattr(ErrorDict, "__html__"))
        self.assertEqual(str(e), e.__html__())