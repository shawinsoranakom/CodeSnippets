def _upload_files(self, params):
        # We use requests.Request to construct our multipart/form-data request
        # here, because they are absurdly fiddly to compose, and Tornado
        # doesn't include a utility for building them. We then use self.fetch()
        # to actually send the request to the test server.
        req = requests.Request(
            method="POST", url=self.get_url("/upload_file"), files=params
        ).prepare()

        return self.fetch(
            "/upload_file", method=req.method, headers=req.headers, body=req.body
        )