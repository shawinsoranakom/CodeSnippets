def test_simple_argument_post(self):
        "Post for a view that has a simple string argument"
        response = self.client.post(reverse("arg_view", args=["Slartibartfast"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Howdy, Slartibartfast")