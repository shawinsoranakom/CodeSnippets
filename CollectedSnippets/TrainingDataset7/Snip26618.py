def get_response(self, req):
        resp = self.client.get(req.path_info)
        for key, value in self.resp_headers.items():
            resp[key] = value
        return resp