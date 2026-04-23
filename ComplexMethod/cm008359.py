def _real_extract(self, url):
        video_id = self._match_id(url)
        data_json = self._download_json(
            f'https://api.divulg.org/post/{video_id}/details', video_id,
            headers={'accept': 'application/json, text/plain, */*'})
        video_json = data_json['video']
        formats, subtitles = [], {}
        for sub in video_json.get('captions') or []:
            sub_url = try_get(sub, lambda x: x['file']['url'])
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('languageCode', 'fr'), []).append({
                'url': sub_url,
            })

        if mpd_url := traverse_obj(video_json, ('dashManifest', 'url', {url_or_none})):
            fmts, subs = self._extract_mpd_formats_and_subtitles(mpd_url, video_id, mpd_id='dash', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if m3u8_url := traverse_obj(video_json, ('hlsManifest', 'url', {url_or_none})):
            fmts, subs = self._extract_m3u8_formats_and_subtitles(m3u8_url, video_id, m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        thumbnails = [{
            'url': image['url'],
            'height': int_or_none(image.get('height')),
            'width': int_or_none(image.get('width')),
        } for image in video_json.get('thumbnails') or [] if image.get('url')]

        return {
            'id': video_id,
            'title': video_json.get('title'),
            'description': video_json.get('description'),
            'view_count': video_json.get('viewCount'),
            'duration': video_json.get('duration'),
            'uploader': try_get(data_json, lambda x: x['channel']['name']),
            'uploader_id': try_get(data_json, lambda x: x['channel']['id']),
            'like_count': data_json.get('likesCount'),
            'upload_date': unified_strdate(video_json.get('publishedAt') or video_json.get('createdAt')),
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
        }