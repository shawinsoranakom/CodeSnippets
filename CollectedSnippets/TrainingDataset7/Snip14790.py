def _get_raw_insecure_uri(self):
        """
        Return an absolute URI from variables available in this request. Skip
        allowed hosts protection, so may return insecure URI.
        """
        return "{scheme}://{host}{path}".format(
            scheme=self.request.scheme,
            host=self.request._get_raw_host(),
            path=self.request.get_full_path(),
        )