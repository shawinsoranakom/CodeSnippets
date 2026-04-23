def test_simple_block_tag_with_context_missing_content(self):
        # The 'content' parameter must be present when takes_context is True
        msg = (
            "'simple_block_tag_with_context_without_content' is decorated with "
            "takes_context=True so it must have a first argument of 'context' and a "
            "second argument of 'content'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().simple_block_tag(takes_context=True)
            def simple_block_tag_with_context_without_content():
                return "Expected result"