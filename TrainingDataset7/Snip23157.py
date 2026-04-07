def test_error_list_html_safe(self):
        e = ErrorList(["Invalid username."])
        self.assertTrue(hasattr(ErrorList, "__html__"))
        self.assertEqual(str(e), e.__html__())