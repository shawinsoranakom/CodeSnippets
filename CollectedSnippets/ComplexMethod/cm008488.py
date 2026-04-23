def _real_extract(self, url):
        video_id = self._match_id(url)
        username, _ = self._get_login_info()
        video_data = self._download_json(
            f'https://api.iwara.tv/video/{video_id}', video_id,
            expected_status=lambda x: True, headers=self._get_media_token())
        errmsg = video_data.get('message')
        # at this point we can actually get uploaded user info, but do we need it?
        if errmsg == 'errors.privateVideo':
            self.raise_login_required('Private video. Login if you have permissions to watch', method='password')
        elif errmsg == 'errors.notFound' and not username:
            self.raise_login_required('Video may need login to view', method='password')
        elif errmsg:  # None if success
            raise ExtractorError(f'Iwara says: {errmsg}')

        if not video_data.get('fileUrl'):
            if video_data.get('embedUrl'):
                return self.url_result(video_data.get('embedUrl'))
            raise ExtractorError('This video is unplayable', expected=True)

        return {
            'id': video_id,
            'age_limit': 18 if video_data.get('rating') == 'ecchi' else 0,  # ecchi is 'sexy' in Japanese
            **traverse_obj(video_data, {
                'title': 'title',
                'description': 'body',
                'uploader': ('user', 'name'),
                'uploader_id': ('user', 'username'),
                'tags': ('tags', ..., 'id'),
                'like_count': 'numLikes',
                'view_count': 'numViews',
                'comment_count': 'numComments',
                'timestamp': ('createdAt', {unified_timestamp}),
                'modified_timestamp': ('updatedAt', {unified_timestamp}),
                'thumbnail': ('file', 'id', {str}, {
                    lambda x: f'https://files.iwara.tv/image/thumbnail/{x}/thumbnail-00.jpg'}),
            }),
            'formats': list(self._extract_formats(video_id, video_data.get('fileUrl'))),
        }