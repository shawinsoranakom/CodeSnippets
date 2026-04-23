def _real_extract(self, url):
        video_type, video_id = self._match_valid_url(url).groups()

        provider = self._PROVIDER_MAP.get(video_type)
        if provider:
            video_id = urllib.parse.unquote(video_id)
            if video_type == 'tumblr-post':
                video_id, blog = video_id.split('-', 1)
                result_url = provider[0] % (blog, video_id)
            elif video_type == 'youtube-list':
                video_id, playlist_id = video_id.split('/')
                result_url = provider[0] % (video_id, playlist_id)
            else:
                result_url = provider[0] + video_id
            return self.url_result('http://' + result_url, provider[1])

        if video_type == 'kinjavideo':
            data = self._download_json(
                'https://kinja.com/api/core/video/views/videoById',
                video_id, query={'videoId': video_id})['data']
            title = data['title']

            formats = []
            for k in ('signedPlaylist', 'streaming'):
                m3u8_url = data.get(k + 'Url')
                if m3u8_url:
                    formats.extend(self._extract_m3u8_formats(
                        m3u8_url, video_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls', fatal=False))

            thumbnail = None
            poster = data.get('poster') or {}
            poster_id = poster.get('id')
            if poster_id:
                thumbnail = 'https://i.kinja-img.com/gawker-media/image/upload/{}.{}'.format(poster_id, poster.get('format') or 'jpg')

            return {
                'id': video_id,
                'title': title,
                'description': strip_or_none(data.get('description')),
                'formats': formats,
                'tags': data.get('tags'),
                'timestamp': int_or_none(try_get(
                    data, lambda x: x['postInfo']['publishTimeMillis']), 1000),
                'thumbnail': thumbnail,
                'uploader': data.get('network'),
            }
        else:
            video_data = self._download_json(
                'https://api.vmh.univision.com/metadata/v1/content/' + video_id,
                video_id)['videoMetadata']
            iptc = video_data['photoVideoMetadataIPTC']
            title = iptc['title']['en']
            fmg = video_data.get('photoVideoMetadata_fmg') or {}
            tvss_domain = fmg.get('tvssDomain') or 'https://auth.univision.com'
            data = self._download_json(
                tvss_domain + '/api/v3/video-auth/url-signature-tokens',
                video_id, query={'mcpids': video_id})['data'][0]
            formats = []

            rendition_url = data.get('renditionUrl')
            if rendition_url:
                formats = self._extract_m3u8_formats(
                    rendition_url, video_id, 'mp4',
                    'm3u8_native', m3u8_id='hls', fatal=False)

            fallback_rendition_url = data.get('fallbackRenditionUrl')
            if fallback_rendition_url:
                formats.append({
                    'format_id': 'fallback',
                    'tbr': int_or_none(self._search_regex(
                        r'_(\d+)\.mp4', fallback_rendition_url,
                        'bitrate', default=None)),
                    'url': fallback_rendition_url,
                })

            return {
                'id': video_id,
                'title': title,
                'thumbnail': try_get(iptc, lambda x: x['cloudinaryLink']['link'], str),
                'uploader': fmg.get('network'),
                'duration': int_or_none(iptc.get('fileDuration')),
                'formats': formats,
                'description': try_get(iptc, lambda x: x['description']['en'], str),
                'timestamp': parse_iso8601(iptc.get('dateReleased')),
            }