def test_methods_with_arguments(self):
        """
        Methods that take arguments should also displayed.
        """
        self.assertContains(self.response, "<h3>Methods with arguments</h3>")
        self.assertContains(self.response, "<td>rename_company</td>")
        self.assertContains(self.response, "<td>dummy_function</td>")
        self.assertContains(self.response, "<td>dummy_function_keyword_only_arg</td>")
        self.assertContains(self.response, "<td>all_kinds_arg_function</td>")
        self.assertContains(self.response, "<td>suffix_company_name</td>")