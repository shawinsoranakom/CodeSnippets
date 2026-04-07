def test_include_tag_missing_context(self):
        # The 'context' parameter must be present when takes_context is True
        msg = (
            "'inclusion_tag_without_context_parameter' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().inclusion_tag("inclusion.html", takes_context=True)
            def inclusion_tag_without_context_parameter(arg):
                return {}