def _get_formats(self, *, ep_id=None, aid=None):
        video_json = self._call_api(
            '/web/playurl', ep_id or aid, note='Downloading video formats',
            errnote='Unable to download video formats', query=filter_dict({
                'platform': 'web',
                'ep_id': ep_id,
                'aid': aid,
            }))
        video_json = video_json['playurl']
        formats = []
        for vid in video_json.get('video') or []:
            video_res = vid.get('video_resource') or {}
            video_info = vid.get('stream_info') or {}
            if not video_res.get('url'):
                continue
            formats.append({
                'url': video_res['url'],
                'ext': 'mp4',
                'format_note': video_info.get('desc_words'),
                'width': video_res.get('width'),
                'height': video_res.get('height'),
                'vbr': video_res.get('bandwidth'),
                'acodec': 'none',
                'vcodec': video_res.get('codecs'),
                'filesize': video_res.get('size'),
            })
        for aud in video_json.get('audio_resource') or []:
            if not aud.get('url'):
                continue
            formats.append({
                'url': aud['url'],
                'ext': 'mp4',
                'abr': aud.get('bandwidth'),
                'acodec': aud.get('codecs'),
                'vcodec': 'none',
                'filesize': aud.get('size'),
            })

        return formats