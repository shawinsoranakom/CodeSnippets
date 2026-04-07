def get_stream_response(request):
            resp = StreamingHttpResponse(self.sequence)
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp