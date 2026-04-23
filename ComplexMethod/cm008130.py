def _call_cdx_api(self, item_id, url, filters: list | None = None, collapse: list | None = None, query: dict | None = None, note=None, fatal=False):
        # CDX docs: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
        query = {
            'url': url,
            'output': 'json',
            'fl': 'original,mimetype,length,timestamp',
            'limit': 500,
            'filter': ['statuscode:200'] + (filters or []),
            'collapse': collapse or [],
            **(query or {}),
        }
        res = self._download_json(
            'https://web.archive.org/cdx/search/cdx', item_id,
            note or 'Downloading CDX API JSON', query=query, fatal=fatal)
        if isinstance(res, list) and len(res) >= 2:
            # format response to make it easier to use
            return [dict(zip(res[0], v)) for v in res[1:]]  # noqa: B905
        elif not isinstance(res, list) or len(res) != 0:
            self.report_warning('Error while parsing CDX API response' + bug_reports_message())