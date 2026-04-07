def test_basic_parse_errors(self):
        for template_name, error_msg in (
            (
                "partial_undefined_name",
                "Partial 'undefined' is not defined in the current template.",
            ),
            ("partial_missing_name", "'partial' tag requires a single argument"),
            ("partial_closing_tag", "Invalid block tag on line 1: 'endpartial'"),
            ("partialdef_missing_name", "'partialdef' tag requires a name"),
            ("partialdef_missing_close_tag", "Unclosed tag on line 1: 'partialdef'"),
            (
                "partialdef_opening_closing_name_mismatch",
                "expected 'endpartialdef' or 'endpartialdef testing-name'.",
            ),
            ("partialdef_invalid_name", "Invalid block tag on line 3: 'endpartialdef'"),
            ("partialdef_extra_params", "'partialdef' tag takes at most 2 arguments"),
            (
                "partialdef_duplicated_names",
                "Partial 'testing-name' is already defined in the "
                "'partialdef_duplicated_names' template.",
            ),
            (
                "partialdef_duplicated_nested_names",
                "Partial 'testing-name' is already defined in the "
                "'partialdef_duplicated_nested_names' template.",
            ),
        ):
            with (
                self.subTest(template_name=template_name),
                self.assertRaisesMessage(TemplateSyntaxError, error_msg),
            ):
                self.engine.render_to_string(template_name)