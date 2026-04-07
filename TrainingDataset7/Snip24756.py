def __call__(self, request):
        response = self.get_response(request)
        # Response.content should be available in the middleware even with a
        # TemplateResponse-based exception response.
        assert response.content
        return response