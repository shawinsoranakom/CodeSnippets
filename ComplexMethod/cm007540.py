def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url, video_id = mobj.group('url', 'id')

        video_id = self._match_id(url)

        data = self._download_json(
            url + '/.json', video_id)[0]['data']['children'][0]['data']

        video_url = data['url']

        # Avoid recursing into the same reddit URL
        if 'reddit.com/' in video_url and '/%s/' % video_id in video_url:
            raise ExtractorError('No media found', expected=True)

        over_18 = data.get('over_18')
        if over_18 is True:
            age_limit = 18
        elif over_18 is False:
            age_limit = 0
        else:
            age_limit = None

        thumbnails = []

        def add_thumbnail(src):
            if not isinstance(src, dict):
                return
            thumbnail_url = url_or_none(src.get('url'))
            if not thumbnail_url:
                return
            thumbnails.append({
                'url': unescapeHTML(thumbnail_url),
                'width': int_or_none(src.get('width')),
                'height': int_or_none(src.get('height')),
            })

        for image in try_get(data, lambda x: x['preview']['images']) or []:
            if not isinstance(image, dict):
                continue
            add_thumbnail(image.get('source'))
            resolutions = image.get('resolutions')
            if isinstance(resolutions, list):
                for resolution in resolutions:
                    add_thumbnail(resolution)

        return {
            '_type': 'url_transparent',
            'url': video_url,
            'title': data.get('title'),
            'thumbnails': thumbnails,
            'timestamp': float_or_none(data.get('created_utc')),
            'uploader': data.get('author'),
            'duration': int_or_none(try_get(
                data,
                (lambda x: x['media']['reddit_video']['duration'],
                 lambda x: x['secure_media']['reddit_video']['duration']))),
            'like_count': int_or_none(data.get('ups')),
            'dislike_count': int_or_none(data.get('downs')),
            'comment_count': int_or_none(data.get('num_comments')),
            'age_limit': age_limit,
        }