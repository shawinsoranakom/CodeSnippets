def _entries(self, data, display_id):
        for page_num in itertools.count(1):
            embedded = data.get('_embedded') or data
            if not isinstance(embedded, dict):
                break
            assets_key = self._extract_assets_key(embedded)
            if not assets_key:
                break
            # Extract entries
            entries = try_get(
                embedded,
                (lambda x: x[assets_key]['_embedded'][assets_key],
                 lambda x: x[assets_key]),
                list)
            for e in self._extract_entries(entries):
                yield e
            # Find next URL
            next_url_path = try_get(
                data,
                (lambda x: x['_links']['next']['href'],
                 lambda x: x['_embedded'][assets_key]['_links']['next']['href']),
                compat_str)
            if not next_url_path:
                break
            data = self._call_api(
                next_url_path, display_id,
                note='Downloading %s JSON page %d' % (assets_key, page_num),
                fatal=False)
            if not data:
                break