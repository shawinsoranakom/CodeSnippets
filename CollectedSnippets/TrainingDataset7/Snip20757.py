def test_decorator_sets_x_frame_options_to_sameorigin(self):
        @xframe_options_sameorigin
        def a_view(request):
            return HttpResponse()

        response = a_view(HttpRequest())
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")