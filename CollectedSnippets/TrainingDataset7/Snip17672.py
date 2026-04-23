def test_view(self):
        """
        login_required is assignable to normal views.
        """

        def normal_view(request):
            pass

        login_required(normal_view)