def test_files(self):
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/raises/")
        self.assertEqual(response.status_code, 500)

        data = {
            "file_data.txt": SimpleUploadedFile("file_data.txt", b"haha"),
        }
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.post("/raises/", data)
        self.assertContains(response, "file_data.txt", status_code=500)
        self.assertNotContains(response, "haha", status_code=500)