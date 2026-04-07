def test_inherited_context(self):
        "Context variables can be retrieved from a list of contexts"
        response = self.client.get("/request_data_extended/", data={"foo": "whiz"})
        self.assertEqual(response.context.__class__, ContextList)
        self.assertEqual(len(response.context), 2)
        self.assertIn("get-foo", response.context)
        self.assertEqual(response.context["get-foo"], "whiz")
        self.assertEqual(response.context["data"], "bacon")

        with self.assertRaisesMessage(KeyError, "does-not-exist"):
            response.context["does-not-exist"]