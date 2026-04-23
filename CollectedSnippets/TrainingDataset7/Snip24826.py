def test_not_allowed(self):
        response = HttpResponseNotAllowed(["GET"])
        self.assertEqual(response.status_code, 405)
        # Standard HttpResponse init args can be used
        response = HttpResponseNotAllowed(
            ["GET"], content="Only the GET method is allowed"
        )
        self.assertContains(response, "Only the GET method is allowed", status_code=405)