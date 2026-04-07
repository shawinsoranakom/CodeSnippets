def _mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request