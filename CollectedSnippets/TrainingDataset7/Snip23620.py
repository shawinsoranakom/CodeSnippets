def test_no_init_args(self):
        """
        A view can't be accidentally instantiated before deployment
        """
        msg = "as_view() takes 1 positional argument but 2 were given"
        with self.assertRaisesMessage(TypeError, msg):
            SimpleView.as_view("value")