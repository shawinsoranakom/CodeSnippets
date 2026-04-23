def assertTemplateNotUsed(self, response=None, template_name=None, msg_prefix=""):
        """
        Assert that the template with the provided name was NOT used in
        rendering the response. Also usable as context manager.
        """
        context_mgr_template, template_names, msg_prefix = self._get_template_used(
            response,
            template_name,
            msg_prefix,
            "assertTemplateNotUsed",
        )
        if context_mgr_template:
            # Use assertTemplateNotUsed as context manager.
            return _AssertTemplateNotUsedContext(self, context_mgr_template, msg_prefix)

        self.assertFalse(
            template_name in template_names,
            msg_prefix
            + "Template '%s' was used unexpectedly in rendering the response"
            % template_name,
        )