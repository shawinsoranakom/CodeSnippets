def close_request(self, request):
        self._close_connections()
        super().close_request(request)