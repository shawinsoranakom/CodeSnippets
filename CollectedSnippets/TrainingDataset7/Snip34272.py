def test_load_annotated_function(self):
        Engine(
            libraries={
                "annotated_tag_function": "template_tests.annotated_tag_function",
            }
        )