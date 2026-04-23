def test_include_tag_missing_context_no_params(self):
        msg = (
            "'inclusion_tag_takes_context_without_params' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):

            @Library().inclusion_tag("inclusion.html", takes_context=True)
            def inclusion_tag_takes_context_without_params():
                return {}