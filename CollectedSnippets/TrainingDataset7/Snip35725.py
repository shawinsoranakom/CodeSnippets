def test_invalid_view(self):
        msg = "view must be a callable or a list/tuple in the case of include()."
        with self.assertRaisesMessage(TypeError, msg):
            path("articles/", "invalid_view")