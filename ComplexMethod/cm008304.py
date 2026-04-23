def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        self._initialize_geo_bypass({
            'countries': smuggled_data.get('geo_countries'),
        })

        mobj = self._match_valid_url(url)
        provider_id = mobj.group('provider_id')
        video_id = mobj.group('id')

        if not provider_id:
            provider_id = 'dJ5BDC'

        path = provider_id + '/'
        if mobj.group('media'):
            path += mobj.group('media')
        path += video_id

        qs_dict = parse_qs(url)
        if 'guid' in qs_dict:
            webpage = self._download_webpage(url, video_id)
            scripts = re.findall(r'<script[^>]+src="([^"]+)"', webpage)
            feed_id = None
            # feed id usually locates in the last script.
            # Seems there's no pattern for the interested script filename, so
            # I try one by one
            for script in reversed(scripts):
                feed_script = self._download_webpage(
                    self._proto_relative_url(script, 'http:'),
                    video_id, 'Downloading feed script')
                feed_id = self._search_regex(
                    r'defaultFeedId\s*:\s*"([^"]+)"', feed_script,
                    'default feed id', default=None)
                if feed_id is not None:
                    break
            if feed_id is None:
                raise ExtractorError('Unable to find feed id')
            return self.url_result('http://feed.theplatform.com/f/{}/{}?byGuid={}'.format(
                provider_id, feed_id, qs_dict['guid'][0]))

        if smuggled_data.get('force_smil_url', False):
            smil_url = url
        # Explicitly specified SMIL (see https://github.com/ytdl-org/youtube-dl/issues/7385)
        elif '/guid/' in url:
            headers = {}
            source_url = smuggled_data.get('source_url')
            if source_url:
                headers['Referer'] = source_url
            request = Request(url, headers=headers)
            webpage = self._download_webpage(request, video_id)
            smil_url = self._search_regex(
                r'<link[^>]+href=(["\'])(?P<url>.+?)\1[^>]+type=["\']application/smil\+xml',
                webpage, 'smil url', group='url')
            path = self._search_regex(
                r'link\.theplatform\.com/s/((?:[^/?#&]+/)+[^/?#&]+)', smil_url, 'path')
            smil_url += '?' if '?' not in smil_url else '&' + 'formats=m3u,mpeg4'
        elif mobj.group('config'):
            config_url = url + '&form=json'
            config_url = config_url.replace('swf/', 'config/')
            config_url = config_url.replace('onsite/', 'onsite/config/')
            config = self._download_json(config_url, video_id, 'Downloading config')
            release_url = config.get('releaseUrl') or f'http://link.theplatform.com/s/{path}?mbr=true'
            smil_url = release_url + '&formats=MPEG4&manifest=f4m'
        else:
            smil_url = f'http://link.theplatform.com/s/{path}?mbr=true'

        sig = smuggled_data.get('sig')
        if sig:
            smil_url = self._sign_url(smil_url, sig['key'], sig['secret'])

        formats, subtitles = self._extract_theplatform_smil(smil_url, video_id)

        # With some sites, manifest URL must be forced to extract HLS formats
        if not traverse_obj(formats, lambda _, v: v['format_id'].startswith('hls')):
            m3u8_url = update_url(url, query='mbr=true&manifest=m3u', fragment=None)
            urlh = self._request_webpage(
                HEADRequest(m3u8_url), video_id, 'Checking for HLS formats', 'No HLS formats found', fatal=False)
            if urlh and urlhandle_detect_ext(urlh) == 'm3u8':
                m3u8_fmts, m3u8_subs = self._extract_m3u8_formats_and_subtitles(
                    m3u8_url, video_id, m3u8_id='hls', fatal=False)
                formats.extend(m3u8_fmts)
                self._merge_subtitles(m3u8_subs, target=subtitles)

        ret = self._extract_theplatform_metadata(path, video_id)
        combined_subtitles = self._merge_subtitles(ret.get('subtitles', {}), subtitles)
        ret.update({
            'id': video_id,
            'formats': formats,
            'subtitles': combined_subtitles,
        })

        return ret