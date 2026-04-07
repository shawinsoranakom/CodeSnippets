def test_correct_exception_index(self):
        tests = [
            (
                "{% load bad_tag %}{% for i in range %}{% badsimpletag %}{% endfor %}",
                (38, 56),
            ),
            (
                "{% load bad_tag %}{% for i in range %}{% for j in range %}"
                "{% badsimpletag %}{% endfor %}{% endfor %}",
                (58, 76),
            ),
            (
                "{% load bad_tag %}{% for i in range %}{% badsimpletag %}"
                "{% for j in range %}Hello{% endfor %}{% endfor %}",
                (38, 56),
            ),
            (
                "{% load bad_tag %}{% for i in range %}{% for j in five %}"
                "{% badsimpletag %}{% endfor %}{% endfor %}",
                (38, 57),
            ),
            (
                "{% load bad_tag %}{% for j in five %}{% badsimpletag %}{% endfor %}",
                (18, 37),
            ),
        ]
        context = Context(
            {
                "range": range(5),
                "five": 5,
            }
        )
        engine = Engine(
            debug=True, libraries={"bad_tag": "template_tests.templatetags.bad_tag"}
        )
        for source, expected_error_source_index in tests:
            template = engine.from_string(source)
            try:
                template.render(context)
            except (RuntimeError, TypeError) as e:
                debug = e.template_debug
                self.assertEqual(
                    (debug["start"], debug["end"]), expected_error_source_index
                )