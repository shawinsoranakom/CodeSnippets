def test_simple_block_tag_missing_context_no_params(self):
        msg = (
            "'simple_tag_takes_context_without_params_block' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().simple_block_tag(takes_context=True)
            def simple_tag_takes_context_without_params_block():
                return "Expected result"