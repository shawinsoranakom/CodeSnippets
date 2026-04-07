def get_request(self):
        self.session = {}
        request = super().get_request()
        request.session = self.session
        return request