def get_response(req):
            resp = self.client.get(req.path_info)
            resp["Last-Modified"] = "Sat, 12 Feb 2011 17:35:44 GMT"
            resp.status_code = 400
            return resp