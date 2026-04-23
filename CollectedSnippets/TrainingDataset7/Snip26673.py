def get_response(req):
            resp = self.client.get(req.path_info)
            resp["ETag"] = "spam"
            resp["Location"] = "/"
            resp.status_code = 301
            return resp