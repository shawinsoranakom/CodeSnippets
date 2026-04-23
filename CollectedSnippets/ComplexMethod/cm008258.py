def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url)
        video_id, is_playlist, playlist_id = self._match_valid_url(url).group('id', 'is_playlist', 'playlist_id')

        if is_playlist:  # We matched the playlist query param as video_id
            playlist_id = video_id
            video_id = None

        if self._yes_playlist(playlist_id, video_id):
            return self.url_result(
                f'http://www.dailymotion.com/playlist/{playlist_id}',
                'DailymotionPlaylist', playlist_id)

        password = self.get_param('videopassword')
        media = self._call_api(
            'media', video_id, '''... on Video {
      %s
      stats {
        likes {
          total
        }
        views {
          total
        }
      }
    }
    ... on Live {
      %s
      audienceCount
      isOnAir
    }''' % (self._COMMON_MEDIA_FIELDS, self._COMMON_MEDIA_FIELDS), 'Downloading media JSON metadata',  # noqa: UP031
            'password: "{}"'.format(self.get_param('videopassword')) if password else None)
        xid = media['xid']

        metadata = self._download_json(
            'https://www.dailymotion.com/player/metadata/video/' + xid,
            xid, 'Downloading metadata JSON',
            query=traverse_obj(smuggled_data, 'query') or {'app': 'com.dailymotion.neon'})

        error = metadata.get('error')
        if error:
            title = error.get('title') or error['raw_message']
            # See https://developer.dailymotion.com/api#access-error
            if error.get('code') == 'DM007':
                allowed_countries = try_get(media, lambda x: x['geoblockedCountries']['allowed'], list)
                self.raise_geo_restricted(msg=title, countries=allowed_countries)
            raise ExtractorError(
                f'{self.IE_NAME} said: {title}', expected=True)

        title = metadata['title']
        is_live = media.get('isOnAir')
        formats = []
        subtitles = {}
        expected_error = None

        for quality, media_list in metadata['qualities'].items():
            for m in media_list:
                media_url = m.get('url')
                media_type = m.get('type')
                if not media_url or media_type == 'application/vnd.lumberjack.manifest':
                    continue
                if media_type == 'application/x-mpegURL':
                    fmt, subs, expected_error = self._extract_dailymotion_m3u8_formats_and_subtitles(
                        media_url, video_id, live=is_live)
                    formats.extend(fmt)
                    self._merge_subtitles(subs, target=subtitles)
                else:
                    f = {
                        'url': media_url,
                        'format_id': 'http-' + quality,
                    }
                    m = re.search(r'/H264-(\d+)x(\d+)(?:-(60)/)?', media_url)
                    if m:
                        width, height, fps = map(int_or_none, m.groups())
                        f.update({
                            'fps': fps,
                            'height': height,
                            'width': width,
                        })
                    formats.append(f)

        if not formats and expected_error:
            self.raise_no_formats(expected_error, expected=True)

        for f in formats:
            f['url'] = f['url'].split('#')[0]
            if not f.get('fps') and f['format_id'].endswith('@60'):
                f['fps'] = 60

        subtitles_data = try_get(metadata, lambda x: x['subtitles']['data'], dict) or {}
        for subtitle_lang, subtitle in subtitles_data.items():
            subtitles[subtitle_lang] = [{
                'url': subtitle_url,
            } for subtitle_url in subtitle.get('urls', [])]

        thumbnails = traverse_obj(metadata, (
            ('posters', 'thumbnails'), {dict.items}, lambda _, v: url_or_none(v[1]), {
                'height': (0, {int_or_none}),
                'id': (0, {str}),
                'url': 1,
            }))

        owner = metadata.get('owner') or {}
        stats = media.get('stats') or {}
        get_count = lambda x: int_or_none(try_get(stats, lambda y: y[x + 's']['total']))

        return {
            'id': video_id,
            'title': title,
            'description': clean_html(media.get('description')),
            'thumbnails': thumbnails,
            'duration': int_or_none(metadata.get('duration')) or None,
            'timestamp': int_or_none(metadata.get('created_time')),
            'uploader': owner.get('screenname'),
            'uploader_id': owner.get('id') or metadata.get('screenname'),
            'age_limit': 18 if metadata.get('explicit') else 0,
            'tags': metadata.get('tags'),
            'view_count': get_count('view') or int_or_none(media.get('audienceCount')),
            'like_count': get_count('like'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }