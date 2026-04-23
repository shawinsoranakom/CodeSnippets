def test_argument_with_space_get(self):
        "Get a view that has a string argument that requires escaping"
        response = self.client.get(reverse("arg_view", args=["Arthur Dent"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hi, Arthur")