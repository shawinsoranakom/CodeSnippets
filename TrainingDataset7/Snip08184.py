def __call__(self, request, *args, **kwargs):
        try:
            obj = self.get_object(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404("Feed object does not exist.")
        feedgen = self.get_feed(obj, request)
        response = HttpResponse(content_type=feedgen.content_type)
        if hasattr(self, "item_pubdate") or hasattr(self, "item_updateddate"):
            # if item_pubdate or item_updateddate is defined for the feed, set
            # header so as ConditionalGetMiddleware can send 304 NOT MODIFIED.
            response.headers["Last-Modified"] = http_date(
                feedgen.latest_post_date().timestamp()
            )
        feedgen.write(response, "utf-8")
        return response