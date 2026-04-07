def get_response(req):
            resp = self.client.get(req.path_info)
            resp["ETag"] = "spam"
            resp.status_code = 400
            return resp