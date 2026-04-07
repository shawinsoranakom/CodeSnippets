def test_single_context(self):
        "Context variables can be retrieved from a single context"
        response = self.client.get("/request_data/", data={"foo": "whiz"})
        self.assertIsInstance(response.context, RequestContext)
        self.assertIn("get-foo", response.context)
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertEqual(response.context["data"], "sausage")

        with self.assertRaisesMessage(KeyError, "does-not-exist"):
            response.context["does-not-exist"]