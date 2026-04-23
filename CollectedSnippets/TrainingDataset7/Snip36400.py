def test_html_safe_defines_html_error(self):
        msg = "can't apply @html_safe to HtmlClass because it defines __html__()."
        with self.assertRaisesMessage(ValueError, msg):

            @html_safe
            class HtmlClass:
                def __html__(self):
                    return "<h1>I'm a html class!</h1>"