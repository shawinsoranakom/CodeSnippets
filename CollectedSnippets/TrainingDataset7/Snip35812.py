def test_redirect_view_object(self):
        from .views import absolute_kwargs_view

        res = redirect(absolute_kwargs_view)
        self.assertEqual(res.url, "/absolute_arg_view/")
        with self.assertRaises(NoReverseMatch):
            redirect(absolute_kwargs_view, wrong_argument=None)