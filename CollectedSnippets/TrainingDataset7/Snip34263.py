def test_inclusion_tags_from_template(self):
        c = Context({"value": 42})

        templates = [
            (
                "{% load inclusion %}{% inclusion_no_params_from_template %}",
                "inclusion_no_params_from_template - Expected result\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_param_from_template 37 %}",
                "inclusion_one_param_from_template - Expected result: 37\n",
            ),
            (
                "{% load inclusion %}"
                "{% inclusion_explicit_no_context_from_template 37 %}",
                "inclusion_explicit_no_context_from_template - Expected result: 37\n",
            ),
            (
                "{% load inclusion %}"
                "{% inclusion_no_params_with_context_from_template %}",
                "inclusion_no_params_with_context_from_template - Expected result "
                "(context value: 42)\n",
            ),
            (
                "{% load inclusion %}"
                "{% inclusion_params_and_context_from_template 37 %}",
                "inclusion_params_and_context_from_template - Expected result (context "
                "value: 42): 37\n",
            ),
            (
                "{% load inclusion %}{% inclusion_two_params_from_template 37 42 %}",
                "inclusion_two_params_from_template - Expected result: 37, 42\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_default_from_template 37 %}",
                "inclusion_one_default_from_template - Expected result: 37, hi\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_default_from_template 37 42 %}",
                "inclusion_one_default_from_template - Expected result: 37, 42\n",
            ),
            (
                "{% load inclusion %}{% inclusion_unlimited_args_from_template 37 %}",
                "inclusion_unlimited_args_from_template - Expected result: 37, hi\n",
            ),
            (
                "{% load inclusion %}"
                "{% inclusion_unlimited_args_from_template 37 42 56 89 %}",
                "inclusion_unlimited_args_from_template - Expected result: 37, 42, 56, "
                "89\n",
            ),
            (
                "{% load inclusion %}{% inclusion_only_unlimited_args_from_template %}",
                "inclusion_only_unlimited_args_from_template - Expected result: \n",
            ),
            (
                "{% load inclusion %}"
                "{% inclusion_only_unlimited_args_from_template 37 42 56 89 %}",
                "inclusion_only_unlimited_args_from_template - Expected result: 37, "
                "42, 56, 89\n",
            ),
        ]

        for entry in templates:
            t = self.engine.from_string(entry[0])
            self.assertEqual(t.render(c), entry[1])