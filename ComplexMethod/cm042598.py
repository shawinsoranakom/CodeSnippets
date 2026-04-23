def _assert_files_downloaded(self, items, logs):
        assert len(items) == 1
        assert self.media_key in items[0]

        # check that logs show the expected number of successful file downloads
        file_dl_success = "File (downloaded): Downloaded file from"
        assert logs.count(file_dl_success) == 3

        # check that the images/files status is `downloaded`
        for item in items:
            for i in item[self.media_key]:
                assert i["status"] == "downloaded"

        # check that the images/files checksums are what we know they should be
        if self.expected_checksums is not None:
            checksums = {i["checksum"] for item in items for i in item[self.media_key]}
            assert checksums == self.expected_checksums

        # check that the image files where actually written to the media store
        for item in items:
            for i in item[self.media_key]:
                assert (self.tmpmediastore / i["path"]).exists()