def test_callable(self):
        """
        login_not_required is assignable to callable objects.
        """

        class CallableView:
            def __call__(self, *args, **kwargs):
                pass

        login_not_required(CallableView())