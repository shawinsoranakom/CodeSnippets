def _per_video_extract(self, smuggled_data, entry_id, info, ks, flavor_assets, captions):
        source_url = smuggled_data.get('source_url')
        if source_url:
            referrer = base64.b64encode(
                '://'.join(urllib.parse.urlparse(source_url)[:2])
                .encode()).decode('utf-8')
        else:
            referrer = None

        def sign_url(unsigned_url):
            if ks:
                unsigned_url += f'/ks/{ks}'
            if referrer:
                unsigned_url += f'?referrer={referrer}'
            return unsigned_url

        data_url = info['dataUrl']
        if '/flvclipper/' in data_url:
            data_url = re.sub(r'/flvclipper/.*', '/serveFlavor', data_url)

        formats = []
        subtitles = {}
        for f in flavor_assets:
            # Continue if asset is not ready
            if f.get('status') != 2:
                continue
            # Original format that's not available (e.g. kaltura:1926081:0_c03e1b5g)
            # skip for now.
            if f.get('fileExt') == 'chun':
                continue
            # DRM-protected video, cannot be decrypted
            if not self.get_param('allow_unplayable_formats') and f.get('fileExt') == 'wvm':
                continue
            if not f.get('fileExt'):
                # QT indicates QuickTime; some videos have broken fileExt
                if f.get('containerFormat') == 'qt':
                    f['fileExt'] = 'mov'
                else:
                    f['fileExt'] = 'mp4'
            video_url = sign_url(
                '{}/flavorId/{}'.format(data_url, f['id']))
            format_id = '{fileExt}-{bitrate}'.format(**f)
            # Source format may not be available (e.g. kaltura:513551:1_66x4rg7o)
            if f.get('isOriginal') is True and not self._is_valid_url(
                    video_url, entry_id, format_id):
                continue
            # audio-only has no videoCodecId (e.g. kaltura:1926081:0_c03e1b5g
            # -f mp4-56)
            vcodec = 'none' if 'videoCodecId' not in f and f.get(
                'frameRate') == 0 else f.get('videoCodecId')
            formats.append({
                'format_id': format_id,
                'ext': f.get('fileExt'),
                'tbr': int_or_none(f['bitrate']),
                'fps': int_or_none(f.get('frameRate')),
                'filesize_approx': int_or_none(f.get('size'), invscale=1024),
                'container': f.get('containerFormat'),
                'vcodec': vcodec,
                'height': int_or_none(f.get('height')),
                'width': int_or_none(f.get('width')),
                'url': video_url,
            })
        if '/playManifest/' in data_url:
            m3u8_url = sign_url(data_url.replace(
                'format/url', 'format/applehttp'))
            fmts, subs = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, entry_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False)
            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        if captions:
            for caption in captions.get('objects', []):
                # Continue if caption is not ready
                if caption.get('status') != 2:
                    continue
                if not caption.get('id'):
                    continue
                caption_format = int_or_none(caption.get('format'))
                subtitles.setdefault(caption.get('languageCode') or caption.get('language'), []).append({
                    'url': '{}/api_v3/service/caption_captionasset/action/serve/captionAssetId/{}'.format(self._SERVICE_URL, caption['id']),
                    'ext': caption.get('fileExt') or self._CAPTION_TYPES.get(caption_format) or 'ttml',
                })

        return {
            'id': entry_id,
            'title': info['name'],
            'formats': formats,
            'subtitles': subtitles,
            'description': clean_html(info.get('description')),
            'thumbnail': info.get('thumbnailUrl'),
            'duration': info.get('duration'),
            'timestamp': info.get('createdAt'),
            'uploader_id': format_field(info, 'userId', ignore=('None', None)),
            'view_count': int_or_none(info.get('plays')),
        }