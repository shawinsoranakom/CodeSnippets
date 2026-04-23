def test_argument_with_space_post(self):
        "Post for a view that has a string argument that requires escaping"
        response = self.client.post(reverse("arg_view", args=["Arthur Dent"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hi, Arthur")