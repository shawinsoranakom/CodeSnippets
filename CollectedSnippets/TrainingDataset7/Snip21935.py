def test_urllib_request_urlopen(self):
        """
        Test the File storage API with a file-like object coming from
        urllib.request.urlopen().
        """
        file_like_object = urlopen(self.live_server_url + "/")
        f = File(file_like_object)
        stored_filename = self.storage.save("remote_file.html", f)

        remote_file = urlopen(self.live_server_url + "/")
        with self.storage.open(stored_filename) as stored_file:
            self.assertEqual(stored_file.read(), remote_file.read())