def _assert_template_used(self, template_name, template_names, msg_prefix, count):
        if not template_names:
            self.fail(msg_prefix + "No templates used to render the response")
        self.assertTrue(
            template_name in template_names,
            msg_prefix + "Template '%s' was not a template used to render"
            " the response. Actual template(s) used: %s"
            % (template_name, ", ".join(template_names)),
        )

        if count is not None:
            self.assertEqual(
                template_names.count(template_name),
                count,
                msg_prefix + "Template '%s' was expected to be rendered %d "
                "time(s) but was actually rendered %d time(s)."
                % (template_name, count, template_names.count(template_name)),
            )