async def get_stream_response(request):
            async def iterator():
                for chunk in self.sequence:
                    yield chunk

            resp = StreamingHttpResponse(iterator())
            resp["Content-Type"] = "text/html; charset=UTF-8"
            return resp