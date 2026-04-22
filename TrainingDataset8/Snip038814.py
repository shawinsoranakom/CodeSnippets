def test_root_level_echo(self):
        import tests.streamlit.echo_test_data.root_level_echo

        echo_str = """```python
a = 123


```"""

        element = self.get_delta_from_queue(0).new_element
        self.assertEqual(echo_str, element.markdown.body)