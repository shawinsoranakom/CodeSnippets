def test_valid_status_code_string(self):
        resp = HttpResponse(status="100")
        self.assertEqual(resp.status_code, 100)
        resp = HttpResponse(status="404")
        self.assertEqual(resp.status_code, 404)
        resp = HttpResponse(status="599")
        self.assertEqual(resp.status_code, 599)