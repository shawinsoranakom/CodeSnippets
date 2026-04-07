def assertTemplateUsed(
        self, response=None, template_name=None, msg_prefix="", count=None
    ):
        """
        Assert that the template with the provided name was used in rendering
        the response. Also usable as context manager.
        """
        context_mgr_template, template_names, msg_prefix = self._get_template_used(
            response,
            template_name,
            msg_prefix,
            "assertTemplateUsed",
        )
        if context_mgr_template:
            # Use assertTemplateUsed as context manager.
            return _AssertTemplateUsedContext(
                self, context_mgr_template, msg_prefix, count
            )

        self._assert_template_used(template_name, template_names, msg_prefix, count)