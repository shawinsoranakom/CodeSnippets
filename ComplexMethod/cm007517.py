def _real_extract(self, url):
        video_id, playlist_id = re.match(self._VALID_URL, url).groups()

        if playlist_id:
            if not self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading playlist %s - add --no-playlist to just download video' % playlist_id)
                return self.url_result(
                    'http://www.dailymotion.com/playlist/' + playlist_id,
                    'DailymotionPlaylist', playlist_id)
            self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        password = self._downloader.params.get('videopassword')
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
    }''' % (self._COMMON_MEDIA_FIELDS, self._COMMON_MEDIA_FIELDS), 'Downloading media JSON metadata',
            'password: "%s"' % self._downloader.params.get('videopassword') if password else None)
        xid = media['xid']

        metadata = self._download_json(
            'https://www.dailymotion.com/player/metadata/video/' + xid,
            xid, 'Downloading metadata JSON',
            query={'app': 'com.dailymotion.neon'})

        error = metadata.get('error')
        if error:
            title = error.get('title') or error['raw_message']
            # See https://developer.dailymotion.com/api#access-error
            if error.get('code') == 'DM007':
                allowed_countries = try_get(media, lambda x: x['geoblockedCountries']['allowed'], list)
                self.raise_geo_restricted(msg=title, countries=allowed_countries)
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, title), expected=True)

        title = metadata['title']
        is_live = media.get('isOnAir')
        formats = []
        for quality, media_list in metadata['qualities'].items():
            for m in media_list:
                media_url = m.get('url')
                media_type = m.get('type')
                if not media_url or media_type == 'application/vnd.lumberjack.manifest':
                    continue
                if media_type == 'application/x-mpegURL':
                    formats.extend(self._extract_m3u8_formats(
                        media_url, video_id, 'mp4',
                        'm3u8' if is_live else 'm3u8_native',
                        m3u8_id='hls', fatal=False))
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
        for f in formats:
            f['url'] = f['url'].split('#')[0]
            if not f.get('fps') and f['format_id'].endswith('@60'):
                f['fps'] = 60
        self._sort_formats(formats)

        subtitles = {}
        subtitles_data = try_get(metadata, lambda x: x['subtitles']['data'], dict) or {}
        for subtitle_lang, subtitle in subtitles_data.items():
            subtitles[subtitle_lang] = [{
                'url': subtitle_url,
            } for subtitle_url in subtitle.get('urls', [])]

        thumbnails = []
        for height, poster_url in metadata.get('posters', {}).items():
            thumbnails.append({
                'height': int_or_none(height),
                'id': height,
                'url': poster_url,
            })

        owner = metadata.get('owner') or {}
        stats = media.get('stats') or {}
        get_count = lambda x: int_or_none(try_get(stats, lambda y: y[x + 's']['total']))

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
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