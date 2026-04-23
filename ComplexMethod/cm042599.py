def _assert_files_download_failure(self, crawler, items, code, logs):
        # check that the item does NOT have the "images/files" field populated
        assert len(items) == 1
        assert self.media_key in items[0]
        assert not items[0][self.media_key]

        # check that there was 1 successful fetch and 3 other responses with non-200 code
        assert crawler.stats.get_value("downloader/request_method_count/GET") == 4
        assert crawler.stats.get_value("downloader/response_count") == 4
        assert crawler.stats.get_value("downloader/response_status_count/200") == 1
        assert crawler.stats.get_value(f"downloader/response_status_count/{code}") == 3

        # check that logs do show the failure on the file downloads
        file_dl_failure = f"File (code: {code}): Error downloading file from"
        assert logs.count(file_dl_failure) == 3

        # check that no files were written to the media store
        assert not list(self.tmpmediastore.iterdir())