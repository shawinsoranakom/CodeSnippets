def test_snake_case_to_camel_case(self):
        """Test streamlit.string_util.snake_case_to_camel_case."""
        self.assertEqual(
            "TestString.", string_util.snake_case_to_camel_case("test_string.")
        )

        self.assertEqual("Init", string_util.snake_case_to_camel_case("__init__"))