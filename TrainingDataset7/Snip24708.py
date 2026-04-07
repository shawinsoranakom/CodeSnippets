def test_data_upload_max_memory_size_exceeded(self):
        response = WSGIHandler()(self.get_suspicious_environ(), lambda *a, **k: None)
        self.assertEqual(response.status_code, 400)