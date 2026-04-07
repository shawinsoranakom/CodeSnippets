def test(self):
        self.test_case._assert_template_used(
            self.template_name,
            self.rendered_template_names,
            self.msg_prefix,
            self.count,
        )