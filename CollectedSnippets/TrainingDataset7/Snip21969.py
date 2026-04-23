def test_stop_upload_temporary_file_handler(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b"a")
            temp_file.seek(0)
            response = self.client.post("/temp_file/stop_upload/", {"file": temp_file})
            temp_path = response.json()["temp_path"]
            self.assertIs(os.path.exists(temp_path), False)