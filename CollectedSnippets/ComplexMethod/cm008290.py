def _real_extract(self, url):
        video_id = self._match_id(url)

        qualities = {
            'lq': '360p',
            'hq': '720p',
        }

        json_url = f'https://www.nuvid.com/player_config_json/?vid={video_id}&aid=0&domain_id=0&embed=0&check_speed=0'
        video_data = self._download_json(
            json_url, video_id, headers={
                'Accept': 'application/json, text/javascript, */*; q = 0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            })

        webpage = self._download_webpage(
            f'http://m.nuvid.com/video/{video_id}',
            video_id, 'Downloading video page', fatal=False) or ''

        title = strip_or_none(video_data.get('title') or self._html_search_regex(
            (r'''<span\s[^>]*?\btitle\s*=\s*(?P<q>"|'|\b)(?P<title>[^"]+)(?P=q)\s*>''',
                r'''<div\s[^>]*?\bclass\s*=\s*(?P<q>"|'|\b)thumb-holder video(?P=q)>\s*<h5\b[^>]*>(?P<title>[^<]+)</h5''',
                r'''<span\s[^>]*?\bclass\s*=\s*(?P<q>"|'|\b)title_thumb(?P=q)>(?P<title>[^<]+)</span'''),
            webpage, 'title', group='title'))

        formats = [{
            'url': source,
            'format_id': qualities.get(quality),
            'height': int_or_none(qualities.get(quality)[:-1]),
        } for quality, source in video_data.get('files').items() if source]

        self._check_formats(formats, video_id)

        duration = parse_duration(traverse_obj(video_data, 'duration', 'duration_format'))
        thumbnails = [
            {'url': thumb_url} for thumb_url in re.findall(
                r'<div\s+class\s*=\s*"video-tmb-wrap"\s*>\s*<img\s+src\s*=\s*"([^"]+)"\s*/>', webpage)
            if url_or_none(thumb_url)]
        if url_or_none(video_data.get('poster')):
            thumbnails.append({'url': video_data['poster'], 'preference': 1})

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnails': thumbnails,
            'duration': duration,
            'age_limit': 18,
        }