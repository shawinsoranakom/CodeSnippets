def get_stream_response_unicode(request):
            resp = StreamingHttpResponse(self.sequence_unicode)
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp