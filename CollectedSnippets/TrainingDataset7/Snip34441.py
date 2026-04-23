def test_response_with_multiple_parts(self):
        context = {}
        template_partials = ["partial_child.html", "partial_child.html#extra-content"]

        response_whole_content_at_once = HttpResponse(
            "".join(
                render_to_string(template_name, context)
                for template_name in template_partials
            )
        )

        response_with_multiple_writes = HttpResponse()
        for template_name in template_partials:
            response_with_multiple_writes.write(
                render_to_string(template_name, context)
            )

        response_with_generator = HttpResponse(
            render_to_string(template_name, context)
            for template_name in template_partials
        )

        for label, response in [
            ("response_whole_content_at_once", response_whole_content_at_once),
            ("response_with_multiple_writes", response_with_multiple_writes),
            ("response_with_generator", response_with_generator),
        ]:
            with self.subTest(response=label):
                self.assertIn(b"Main Content", response.content)
                self.assertIn(b"Extra Content", response.content)