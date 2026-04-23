def test_simple_block_tag_missing_content(self):
        # The 'content' parameter must be present when takes_context is True
        msg = (
            "'simple_block_tag_without_content' must have a first argument of 'content'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().simple_block_tag
            def simple_block_tag_without_content():
                return "Expected result"