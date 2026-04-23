def process_request(self, request):
        request._csp_nonce = LazyNonce()