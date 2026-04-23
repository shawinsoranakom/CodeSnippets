def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        partner_id, entry_id = mobj.group('partner_id', 'id')
        ks = None
        captions = None
        if partner_id and entry_id:
            _, info, flavor_assets, captions = self._get_video_info(entry_id, partner_id, smuggled_data.get('service_url'))
        else:
            path, query = mobj.group('path', 'query')
            if not path and not query:
                raise ExtractorError('Invalid URL', expected=True)
            params = {}
            if query:
                params = compat_parse_qs(query)
            if path:
                splitted_path = path.split('/')
                params.update(dict((zip(splitted_path[::2], [[v] for v in splitted_path[1::2]]))))
            if 'wid' in params:
                partner_id = params['wid'][0][1:]
            elif 'p' in params:
                partner_id = params['p'][0]
            elif 'partner_id' in params:
                partner_id = params['partner_id'][0]
            else:
                raise ExtractorError('Invalid URL', expected=True)
            if 'entry_id' in params:
                entry_id = params['entry_id'][0]
                _, info, flavor_assets, captions = self._get_video_info(entry_id, partner_id)
            elif 'uiconf_id' in params and 'flashvars[referenceId]' in params:
                reference_id = params['flashvars[referenceId]'][0]
                webpage = self._download_webpage(url, reference_id)
                entry_data = self._parse_json(self._search_regex(
                    r'window\.kalturaIframePackageData\s*=\s*({.*});',
                    webpage, 'kalturaIframePackageData'),
                    reference_id)['entryResult']
                info, flavor_assets = entry_data['meta'], entry_data['contextData']['flavorAssets']
                entry_id = info['id']
                # Unfortunately, data returned in kalturaIframePackageData lacks
                # captions so we will try requesting the complete data using
                # regular approach since we now know the entry_id
                try:
                    _, info, flavor_assets, captions = self._get_video_info(
                        entry_id, partner_id)
                except ExtractorError:
                    # Regular scenario failed but we already have everything
                    # extracted apart from captions and can process at least
                    # with this
                    pass
            else:
                raise ExtractorError('Invalid URL', expected=True)
            ks = params.get('flashvars[ks]', [None])[0]

        source_url = smuggled_data.get('source_url')
        if source_url:
            referrer = base64.b64encode(
                '://'.join(compat_urlparse.urlparse(source_url)[:2])
                .encode('utf-8')).decode('utf-8')
        else:
            referrer = None

        def sign_url(unsigned_url):
            if ks:
                unsigned_url += '/ks/%s' % ks
            if referrer:
                unsigned_url += '?referrer=%s' % referrer
            return unsigned_url

        data_url = info['dataUrl']
        if '/flvclipper/' in data_url:
            data_url = re.sub(r'/flvclipper/.*', '/serveFlavor', data_url)

        formats = []
        for f in flavor_assets:
            # Continue if asset is not ready
            if f.get('status') != 2:
                continue
            # Original format that's not available (e.g. kaltura:1926081:0_c03e1b5g)
            # skip for now.
            if f.get('fileExt') == 'chun':
                continue
            # DRM-protected video, cannot be decrypted
            if f.get('fileExt') == 'wvm':
                continue
            if not f.get('fileExt'):
                # QT indicates QuickTime; some videos have broken fileExt
                if f.get('containerFormat') == 'qt':
                    f['fileExt'] = 'mov'
                else:
                    f['fileExt'] = 'mp4'
            video_url = sign_url(
                '%s/flavorId/%s' % (data_url, f['id']))
            format_id = '%(fileExt)s-%(bitrate)s' % f
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
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, entry_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        self._sort_formats(formats)

        subtitles = {}
        if captions:
            for caption in captions.get('objects', []):
                # Continue if caption is not ready
                if caption.get('status') != 2:
                    continue
                if not caption.get('id'):
                    continue
                caption_format = int_or_none(caption.get('format'))
                subtitles.setdefault(caption.get('languageCode') or caption.get('language'), []).append({
                    'url': '%s/api_v3/service/caption_captionasset/action/serve/captionAssetId/%s' % (self._SERVICE_URL, caption['id']),
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
            'uploader_id': info.get('userId') if info.get('userId') != 'None' else None,
            'view_count': int_or_none(info.get('plays')),
        }