def test_view(self):
        """
        login_not_required is assignable to normal views.
        """

        def normal_view(request):
            pass

        login_not_required(normal_view)