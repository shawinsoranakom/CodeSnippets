def test_context_processor_priority(self):
        # context processors should be overridden by passed-in context
        response = self._response(
            "{{ foo }}{{ processors }}", {"processors": "no"}
        ).render()
        self.assertEqual(response.content, b"no")