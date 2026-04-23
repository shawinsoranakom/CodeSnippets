def download(self, url_list):
        """Download a given list of URLs."""
        outtmpl = self.params.get('outtmpl', DEFAULT_OUTTMPL)
        if (len(url_list) > 1
                and outtmpl != '-'
                and '%' not in outtmpl
                and self.params.get('max_downloads') != 1):
            raise SameFileError(outtmpl)

        for url in url_list:
            try:
                # It also downloads the videos
                res = self.extract_info(
                    url, force_generic_extractor=self.params.get('force_generic_extractor', False))
            except UnavailableVideoError:
                self.report_error('unable to download video')
            except MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloaded files reached.')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    self.to_stdout(json.dumps(self.sanitize_info(res)))

        return self._download_retcode