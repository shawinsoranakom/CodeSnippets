def get_success_url_allowed_hosts(self, request=None):
        if request is None:
            request = self.request
        return {request.get_host(), *self.success_url_allowed_hosts}