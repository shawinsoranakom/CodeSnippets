def get_response(self, req):
        return self.client.get(req.path)