def _real_extract(self, url):
        shared_name, file_id, service = self._match_valid_url(url).group('shared_name', 'id', 'service')
        webpage = self._download_webpage(url, file_id or shared_name)

        if not file_id:
            post_stream_data = self._search_json(
                r'Box\.postStreamData\s*=', webpage, 'Box post-stream data', shared_name)
            shared_item = traverse_obj(
                post_stream_data, ('/app-api/enduserapp/shared-item', {dict})) or {}
            if shared_item.get('itemType') != 'file':
                raise ExtractorError('The requested resource is not a file', expected=True)

            file_id = str(shared_item['itemID'])

        request_token = self._search_json(
            r'Box\.config\s*=', webpage, 'Box config', file_id)['requestToken']
        access_token = self._download_json(
            f'https://{service}.box.com/app-api/enduserapp/elements/tokens', file_id,
            'Downloading token JSON metadata',
            data=json.dumps({'fileIDs': [file_id]}).encode(), headers={
                'Content-Type': 'application/json',
                'X-Request-Token': request_token,
                'X-Box-EndUser-API': 'sharedName=' + shared_name,
            })[file_id]['read']
        shared_link = f'https://{service}.box.com/s/{shared_name}'
        f = self._download_json(
            'https://api.box.com/2.0/files/' + file_id, file_id,
            'Downloading file JSON metadata', headers={
                'Authorization': 'Bearer ' + access_token,
                'BoxApi': 'shared_link=' + shared_link,
                'X-Rep-Hints': '[dash]',  # TODO: extract `hls` formats
            }, query={
                'fields': 'authenticated_download_url,created_at,created_by,description,extension,is_download_available,name,representations,size',
            })
        title = f['name']

        query = {
            'access_token': access_token,
            'shared_link': shared_link,
        }

        formats = []

        for url_tmpl in traverse_obj(f, (
            'representations', 'entries', lambda _, v: v['representation'] == 'dash',
            'content', 'url_template', {url_or_none},
        )):
            manifest_url = update_url_query(url_tmpl.replace('{+asset_path}', 'manifest.mpd'), query)
            fmts = self._extract_mpd_formats(manifest_url, file_id)
            for fmt in fmts:
                fmt['extra_param_to_segment_url'] = urllib.parse.urlparse(manifest_url).query
            formats.extend(fmts)

        creator = f.get('created_by') or {}

        return {
            'id': file_id,
            'title': title,
            'formats': formats,
            'description': f.get('description') or None,
            'uploader': creator.get('name'),
            'timestamp': parse_iso8601(f.get('created_at')),
            'uploader_id': creator.get('id'),
        }