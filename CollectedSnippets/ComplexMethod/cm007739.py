def _extract(self, content_tree_url, video_id, domain=None, supportedformats=None, embed_token=None):
        content_tree = self._download_json(content_tree_url, video_id)['content_tree']
        metadata = content_tree[list(content_tree)[0]]
        embed_code = metadata['embed_code']
        pcode = metadata.get('asset_pcode') or embed_code
        title = metadata['title']

        auth_data = self._download_json(
            self._AUTHORIZATION_URL_TEMPLATE % (pcode, embed_code),
            video_id, headers=self.geo_verification_headers(), query={
                'domain': domain or 'player.ooyala.com',
                'supportedFormats': supportedformats or 'mp4,rtmp,m3u8,hds,dash,smooth',
                'embedToken': embed_token,
            })['authorization_data'][embed_code]

        urls = []
        formats = []
        streams = auth_data.get('streams') or [{
            'delivery_type': 'hls',
            'url': {
                'data': base64.b64encode(('http://player.ooyala.com/hls/player/all/%s.m3u8' % embed_code).encode()).decode(),
            }
        }]
        for stream in streams:
            url_data = try_get(stream, lambda x: x['url']['data'], compat_str)
            if not url_data:
                continue
            s_url = compat_b64decode(url_data).decode('utf-8')
            if not s_url or s_url in urls:
                continue
            urls.append(s_url)
            ext = determine_ext(s_url, None)
            delivery_type = stream.get('delivery_type')
            if delivery_type == 'hls' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    re.sub(r'/ip(?:ad|hone)/', '/all/', s_url), embed_code, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif delivery_type == 'hds' or ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    s_url + '?hdcore=3.7.0', embed_code, f4m_id='hds', fatal=False))
            elif delivery_type == 'dash' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    s_url, embed_code, mpd_id='dash', fatal=False))
            elif delivery_type == 'smooth':
                self._extract_ism_formats(
                    s_url, embed_code, ism_id='mss', fatal=False)
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    s_url, embed_code, fatal=False))
            else:
                formats.append({
                    'url': s_url,
                    'ext': ext or delivery_type,
                    'vcodec': stream.get('video_codec'),
                    'format_id': delivery_type,
                    'width': int_or_none(stream.get('width')),
                    'height': int_or_none(stream.get('height')),
                    'abr': int_or_none(stream.get('audio_bitrate')),
                    'vbr': int_or_none(stream.get('video_bitrate')),
                    'fps': float_or_none(stream.get('framerate')),
                })
        if not formats and not auth_data.get('authorized'):
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, auth_data['message']), expected=True)
        self._sort_formats(formats)

        subtitles = {}
        for lang, sub in metadata.get('closed_captions_vtt', {}).get('captions', {}).items():
            sub_url = sub.get('url')
            if not sub_url:
                continue
            subtitles[lang] = [{
                'url': sub_url,
            }]

        return {
            'id': embed_code,
            'title': title,
            'description': metadata.get('description'),
            'thumbnail': metadata.get('thumbnail_image') or metadata.get('promo_image'),
            'duration': float_or_none(metadata.get('duration'), 1000),
            'subtitles': subtitles,
            'formats': formats,
        }