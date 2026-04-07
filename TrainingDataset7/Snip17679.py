def test_decorator_marks_view_as_login_not_required(self):
        @login_not_required
        def view(request):
            return HttpResponse()

        self.assertFalse(view.login_required)