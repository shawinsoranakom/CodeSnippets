def test_post_callbacks(self):
        "Rendering a template response triggers the post-render callbacks"
        post = []

        def post1(obj):
            post.append("post1")

        def post2(obj):
            post.append("post2")

        response = SimpleTemplateResponse("first/test.html", {})
        response.add_post_render_callback(post1)
        response.add_post_render_callback(post2)

        # When the content is rendered, all the callbacks are invoked, too.
        response.render()
        self.assertEqual(response.content, b"First template\n")
        self.assertEqual(post, ["post1", "post2"])