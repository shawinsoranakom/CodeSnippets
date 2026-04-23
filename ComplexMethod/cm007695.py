def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video = self._download_json(
            'http://vube.com/t-api/v1/video/%s' % video_id, video_id, 'Downloading video JSON')

        public_id = video['public_id']

        formats = []

        for media in video['media'].get('video', []) + video['media'].get('audio', []):
            if media['transcoding_status'] != 'processed':
                continue
            fmt = {
                'url': 'http://video.thestaticvube.com/video/%s/%s.mp4' % (media['media_resolution_id'], public_id),
                'abr': int(media['audio_bitrate']),
                'format_id': compat_str(media['media_resolution_id']),
            }
            vbr = int(media['video_bitrate'])
            if vbr:
                fmt.update({
                    'vbr': vbr,
                    'height': int(media['height']),
                })
            formats.append(fmt)

        self._sort_formats(formats)

        if not formats and video.get('vst') == 'dmca':
            raise ExtractorError(
                'This video has been removed in response to a complaint received under the US Digital Millennium Copyright Act.',
                expected=True)

        title = video['title']
        description = video.get('description')
        thumbnail = self._proto_relative_url(video.get('thumbnail_src'), scheme='http:')
        uploader = video.get('user_alias') or video.get('channel')
        timestamp = int_or_none(video.get('upload_time'))
        duration = video['duration']
        view_count = video.get('raw_view_count')
        like_count = video.get('total_likes')
        dislike_count = video.get('total_hates')

        comments = video.get('comments')
        comment_count = None
        if comments is None:
            comment_data = self._download_json(
                'http://vube.com/api/video/%s/comment' % video_id,
                video_id, 'Downloading video comment JSON', fatal=False)
            if comment_data is not None:
                comment_count = int_or_none(comment_data.get('total'))
        else:
            comment_count = len(comments)

        categories = [tag['text'] for tag in video['tags']]

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'categories': categories,
        }