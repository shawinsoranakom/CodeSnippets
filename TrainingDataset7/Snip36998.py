def test_server_error(self):
        "The server_error view raises a 500 status"
        response = self.client.get("/server_error/")
        self.assertContains(response, b"<h1>Server Error (500)</h1>", status_code=500)