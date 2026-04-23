def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_ld = self._search_json_ld(webpage, video_id)
        nextjs_data = self._search_nextjs_data(webpage, video_id)

        media_data = (
            traverse_obj(
                nextjs_data, ('props', 'pageProps', ('data', 'OpenGraphParameters')), get_all=False)
            or self._download_json(f'https://yappy.media/api/video/{video_id}', video_id))

        media_url = traverse_obj(media_data, ('link', {url_or_none})) or ''
        has_watermark = media_url.endswith('-wm.mp4')

        formats = [{
            'url': media_url,
            'ext': 'mp4',
            'format_note': 'Watermarked' if has_watermark else None,
            'preference': -10 if has_watermark else None,
        }] if media_url else []

        if has_watermark:
            formats.append({
                'url': media_url.replace('-wm.mp4', '.mp4'),
                'ext': 'mp4',
            })

        audio_link = traverse_obj(media_data, ('audio', 'link'))
        if audio_link:
            formats.append({
                'url': audio_link,
                'ext': 'mp3',
                'acodec': 'mp3',
                'vcodec': 'none',
            })

        return {
            'id': video_id,
            'title': (json_ld.get('description') or self._html_search_meta(['og:title'], webpage)
                      or self._html_extract_title(webpage)),
            'formats': formats,
            'thumbnail': (media_data.get('thumbnail')
                          or self._html_search_meta(['og:image', 'og:image:secure_url'], webpage)),
            'description': (media_data.get('description') or json_ld.get('description')
                            or self._html_search_meta(['description', 'og:description'], webpage)),
            'timestamp': unified_timestamp(media_data.get('publishedAt') or json_ld.get('timestamp')),
            'view_count': int_or_none(media_data.get('viewsCount') or json_ld.get('view_count')),
            'like_count': int_or_none(media_data.get('likesCount')),
            'uploader': traverse_obj(media_data, ('creator', 'firstName')),
            'uploader_id': traverse_obj(media_data, ('creator', ('uuid', 'nickname')), get_all=False),
            'categories': traverse_obj(media_data, ('categories', ..., 'name')) or None,
            'repost_count': int_or_none(media_data.get('sharingCount')),
        }