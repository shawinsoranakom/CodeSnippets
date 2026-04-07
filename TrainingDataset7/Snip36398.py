def test_html_safe(self):
        @html_safe
        class HtmlClass:
            def __str__(self):
                return "<h1>I'm a html class!</h1>"

        html_obj = HtmlClass()
        self.assertTrue(hasattr(HtmlClass, "__html__"))
        self.assertTrue(hasattr(html_obj, "__html__"))
        self.assertEqual(str(html_obj), html_obj.__html__())