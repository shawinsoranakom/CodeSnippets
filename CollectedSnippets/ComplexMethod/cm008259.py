def _entries(self, file_id):
        query_params = {}
        if password := self.get_param('videopassword'):
            query_params['password'] = hashlib.sha256(password.encode()).hexdigest()

        files = self._download_json(
            f'https://api.gofile.io/contents/{file_id}', file_id, 'Getting filelist',
            query=query_params, headers={
                'Authorization': f'Bearer {self._TOKEN}',
                'X-Website-Token': self._STATIC_TOKEN,
            })

        status = files['status']
        if status == 'error-passwordRequired':
            raise ExtractorError(
                'This video is protected by a password, use the --video-password option', expected=True)
        elif status != 'ok':
            raise ExtractorError(f'{self.IE_NAME} said: status {status}', expected=True)

        found_files = False
        for file in (try_get(files, lambda x: x['data']['children'], dict) or {}).values():
            file_type, file_format = file.get('mimetype').split('/', 1)
            if file_type not in ('video', 'audio') and file_format != 'vnd.mts':
                continue

            found_files = True
            file_url = file.get('link')
            if file_url:
                yield {
                    'id': file['id'],
                    'title': file['name'].rsplit('.', 1)[0],
                    'url': file_url,
                    'filesize': file.get('size'),
                    'release_timestamp': file.get('createTime'),
                }

        if not found_files:
            raise ExtractorError('No video/audio found at provided URL.', expected=True)