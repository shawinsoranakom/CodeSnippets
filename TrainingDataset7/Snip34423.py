def test_cannot_parse_characters(self):
        p = Parser("", builtins=[filter_library])
        for filter_expression, characters in [
            ('<>|default:"Default"|upper', '|<>||default:"Default"|upper'),
            ("test|<>|upper", "test||<>||upper"),
        ]:
            with self.subTest(filter_expression=filter_expression):
                with self.assertRaisesMessage(
                    TemplateSyntaxError,
                    f"Could not parse some characters: {characters}",
                ):
                    FilterExpression(filter_expression, p)