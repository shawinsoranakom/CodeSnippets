def process_view(self, *args, **kwargs):
        def stream():
            yield reverse("outer")

        return StreamingHttpResponse(stream())