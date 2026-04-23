def test_no_init_kwargs(self):
        """
        A view can't be accidentally instantiated before deployment
        """
        msg = "This method is available only on the class, not on instances."
        with self.assertRaisesMessage(AttributeError, msg):
            SimpleView(key="value").as_view()