def _get_subtitles(self, video_id, domain):
        info = self._download_json(f'https://pcweb.api.mgtv.com/video/title?videoId={video_id}',
                                   video_id, fatal=False) or {}
        subtitles = {}
        for sub in try_get(info, lambda x: x['data']['title']) or []:
            url_sub = sub.get('url')
            if not url_sub:
                continue
            locale = sub.get('captionSimpleName') or 'en'
            sub = self._download_json(f'{domain}{url_sub}', video_id, fatal=False,
                                      note=f'Download subtitle for locale {sub.get("name")} ({locale})') or {}
            sub_url = url_or_none(sub.get('info'))
            if not sub_url:
                continue
            subtitles.setdefault(locale.lower(), []).append({
                'url': sub_url,
                'name': sub.get('name'),
                'ext': 'srt',
            })
        return subtitles