def test_pickling(self):
        # Create a template response. The context is
        # known to be unpicklable (e.g., a function).
        response = TemplateResponse(
            self.factory.get("/"),
            "first/test.html",
            {
                "value": 123,
                "fn": datetime.now,
            },
        )
        with self.assertRaises(ContentNotRenderedError):
            pickle.dumps(response)

        # But if we render the response, we can pickle it.
        response.render()
        pickled_response = pickle.dumps(response)
        unpickled_response = pickle.loads(pickled_response)

        self.assertEqual(unpickled_response.content, response.content)
        self.assertEqual(
            unpickled_response.headers["content-type"], response.headers["content-type"]
        )
        self.assertEqual(unpickled_response.status_code, response.status_code)

        # ...and the unpickled response doesn't have the
        # template-related attributes, so it can't be re-rendered
        template_attrs = (
            "template_name",
            "context_data",
            "_post_render_callbacks",
            "_request",
        )
        for attr in template_attrs:
            self.assertFalse(hasattr(unpickled_response, attr))

        # ...and requesting any of those attributes raises an exception
        for attr in template_attrs:
            with self.assertRaises(AttributeError):
                getattr(unpickled_response, attr)