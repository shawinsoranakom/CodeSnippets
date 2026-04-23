def _real_extract(self, url):

        is_m = 'm.ximalaya' in url
        scheme = 'https' if url.startswith('https') else 'http'

        audio_id = self._match_id(url)
        webpage = self._download_webpage(url, audio_id,
                                         note='Download sound page for %s' % audio_id,
                                         errnote='Unable to get sound page')

        audio_info_file = '%s://m.ximalaya.com/tracks/%s.json' % (scheme, audio_id)
        audio_info = self._download_json(audio_info_file, audio_id,
                                         'Downloading info json %s' % audio_info_file,
                                         'Unable to download info file')

        formats = []
        for bps, k in (('24k', 'play_path_32'), ('64k', 'play_path_64')):
            if audio_info.get(k):
                formats.append({
                    'format_id': bps,
                    'url': audio_info[k],
                })

        thumbnails = []
        for k in audio_info.keys():
            # cover pics kyes like: cover_url', 'cover_url_142'
            if k.startswith('cover_url'):
                thumbnail = {'name': k, 'url': audio_info[k]}
                if k == 'cover_url_142':
                    thumbnail['width'] = 180
                    thumbnail['height'] = 180
                thumbnails.append(thumbnail)

        audio_uploader_id = audio_info.get('uid')

        if is_m:
            audio_description = self._html_search_regex(r'(?s)<section\s+class=["\']content[^>]+>(.+?)</section>',
                                                        webpage, 'audio_description', fatal=False)
        else:
            audio_description = self._html_search_regex(r'(?s)<div\s+class=["\']rich_intro[^>]*>(.+?</article>)',
                                                        webpage, 'audio_description', fatal=False)

        if not audio_description:
            audio_description_file = '%s://www.ximalaya.com/sounds/%s/rich_intro' % (scheme, audio_id)
            audio_description = self._download_webpage(audio_description_file, audio_id,
                                                       note='Downloading description file %s' % audio_description_file,
                                                       errnote='Unable to download descrip file',
                                                       fatal=False)
            audio_description = audio_description.strip() if audio_description else None

        return {
            'id': audio_id,
            'uploader': audio_info.get('nickname'),
            'uploader_id': audio_uploader_id,
            'uploader_url': self._USER_URL_FORMAT % (scheme, audio_uploader_id) if audio_uploader_id else None,
            'title': audio_info['title'],
            'thumbnails': thumbnails,
            'description': audio_description,
            'categories': list(filter(None, (audio_info.get('category_name'), audio_info.get('category_title')))),
            'duration': audio_info.get('duration'),
            'view_count': audio_info.get('play_count'),
            'like_count': audio_info.get('favorites_count'),
            'formats': formats,
        }