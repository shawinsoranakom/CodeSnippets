def process_view(self, *args, **kwargs):
        def stream():
            yield reverse("inner")

        return StreamingHttpResponse(stream())