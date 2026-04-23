def test_simple_argument_get(self):
        "Get a view that has a simple string argument"
        response = self.client.get(reverse("arg_view", args=["Slartibartfast"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Howdy, Slartibartfast")