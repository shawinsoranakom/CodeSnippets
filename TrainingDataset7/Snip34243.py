def test_simple_tag_missing_context_no_params(self):
        msg = (
            "'simple_tag_takes_context_without_params' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().simple_tag(takes_context=True)
            def simple_tag_takes_context_without_params():
                return "Expected result"