def _extract_embeds(self, url, webpage, *, urlh=None, info_dict={}):
        """Returns an iterator of video entries"""
        info_dict = types.MappingProxyType(info_dict)  # Prevents accidental mutation
        video_id = traverse_obj(info_dict, 'display_id', 'id') or self._generic_id(url)
        url, smuggled_data = unsmuggle_url(url, {})
        actual_url = urlh.url if urlh else url

        # Sometimes embedded video player is hidden behind percent encoding
        # (e.g. https://github.com/ytdl-org/youtube-dl/issues/2448)
        # Unescaping the whole page allows to handle those cases in a generic way
        # FIXME: unescaping the whole page may break URLs, commenting out for now.
        # There probably should be a second run of generic extractor on unescaped webpage.
        # webpage = urllib.parse.unquote(webpage)

        embeds = []
        for ie in self._downloader._ies.values():
            if ie.ie_key() in smuggled_data.get('block_ies', []):
                continue
            gen = ie.extract_from_webpage(self._downloader, url, webpage)
            current_embeds = []
            try:
                while True:
                    current_embeds.append(next(gen))
            except self.StopExtraction:
                self.report_detected(f'{ie.IE_NAME} exclusive embed', len(current_embeds),
                                     embeds and 'discarding other embeds')
                return current_embeds
            except StopIteration:
                self.report_detected(f'{ie.IE_NAME} embed', len(current_embeds))
                embeds.extend(current_embeds)

        if embeds:
            return embeds

        jwplayer_data = self._find_jwplayer_data(
            webpage, video_id, transform_source=js_to_json)
        if jwplayer_data:
            if isinstance(jwplayer_data.get('playlist'), str):
                self.report_detected('JW Player playlist')
                return [self.url_result(jwplayer_data['playlist'], 'JWPlatform')]
            try:
                info = self._parse_jwplayer_data(
                    jwplayer_data, video_id, require_title=False, base_url=url)
                if traverse_obj(info, 'formats', ('entries', ..., 'formats')):
                    self.report_detected('JW Player data')
                    return [info]
            except ExtractorError:
                # See https://github.com/ytdl-org/youtube-dl/pull/16735
                pass

        # Video.js embed
        mobj = re.search(
            r'(?s)\bvideojs\s*\(.+?([a-zA-Z0-9_$]+)\.src\s*\(\s*((?:\[.+?\]|{.+?}))\s*\)\s*;',
            webpage)
        if mobj is not None:
            varname = mobj.group(1)
            sources = variadic(self._parse_json(
                mobj.group(2), video_id, transform_source=js_to_json, fatal=False) or [])
            formats, subtitles, src = [], {}, None
            for source in sources:
                src = source.get('src')
                if not src or not isinstance(src, str):
                    continue
                src = urllib.parse.urljoin(url, src)
                src_type = source.get('type')
                if isinstance(src_type, str):
                    src_type = src_type.lower()
                ext = determine_ext(src).lower()
                if src_type == 'video/youtube':
                    return [self.url_result(src, YoutubeIE.ie_key())]
                if src_type == 'application/dash+xml' or ext == 'mpd':
                    fmts, subs = self._extract_mpd_formats_and_subtitles(
                        src, video_id, mpd_id='dash', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)
                elif src_type == 'application/x-mpegurl' or ext == 'm3u8':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        src, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)

                if not formats:
                    formats.append({
                        'url': src,
                        'ext': (mimetype2ext(src_type)
                                or ext if ext in KNOWN_EXTENSIONS else 'mp4'),
                        'http_headers': {
                            'Referer': actual_url,
                        },
                    })
            # https://docs.videojs.com/player#addRemoteTextTrack
            # https://html.spec.whatwg.org/multipage/media.html#htmltrackelement
            for sub_match in re.finditer(rf'(?s){re.escape(varname)}' + r'\.addRemoteTextTrack\(({.+?})\s*,\s*(?:true|false)\)', webpage):
                sub = self._parse_json(
                    sub_match.group(1), video_id, transform_source=js_to_json, fatal=False) or {}
                sub_src = str_or_none(sub.get('src'))
                if not sub_src:
                    continue
                subtitles.setdefault(dict_get(sub, ('language', 'srclang')) or 'und', []).append({
                    'url': urllib.parse.urljoin(url, sub_src),
                    'name': sub.get('label'),
                    'http_headers': {
                        'Referer': actual_url,
                    },
                })
            if formats or subtitles:
                self.report_detected('video.js embed')
                info_dict = {'formats': formats, 'subtitles': subtitles}
                if formats:
                    self._extra_manifest_info(info_dict, src)
                return [info_dict]

        # Look for generic KVS player (before json-ld bc of some urls that break otherwise)
        found = self._search_regex((
            r'<script\b[^>]+?\bsrc\s*=\s*(["\'])https?://(?:(?!\1)[^?#])+/kt_player\.js\?v=(?P<ver>\d+(?:\.\d+)+)\1[^>]*>',
            r'kt_player\s*\(\s*(["\'])(?:(?!\1)[\w\W])+\1\s*,\s*(["\'])https?://(?:(?!\2)[^?#])+/kt_player\.swf\?v=(?P<ver>\d+(?:\.\d+)+)\2\s*,',
        ), webpage, 'KVS player', group='ver', default=False)
        if found:
            self.report_detected('KVS Player')
            if found.split('.')[0] not in ('4', '5', '6'):
                self.report_warning(f'Untested major version ({found}) in player engine - download may fail.')
            return [self._extract_kvs(url, webpage, video_id)]

        # Looking for http://schema.org/VideoObject
        json_ld = self._search_json_ld(webpage, video_id, default={})
        if json_ld.get('url') not in (url, None):
            self.report_detected('JSON LD')
            is_direct = json_ld.get('ext') not in (None, *MEDIA_EXTENSIONS.manifests)
            return [merge_dicts({
                '_type': 'video' if is_direct else 'url_transparent',
                'url': smuggle_url(json_ld['url'], {
                    'force_videoid': video_id,
                    'to_generic': True,
                    'referer': url,
                }),
            }, json_ld)]

        def check_video(vurl):
            if YoutubeIE.suitable(vurl):
                return True
            if RtmpIE.suitable(vurl):
                return True
            vpath = urllib.parse.urlparse(vurl).path
            vext = determine_ext(vpath, None)
            return vext not in (None, 'swf', 'png', 'jpg', 'srt', 'sbv', 'sub', 'vtt', 'ttml', 'js', 'xml')

        def filter_video(urls):
            return list(filter(check_video, urls))

        # Start with something easy: JW Player in SWFObject
        found = filter_video(re.findall(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage))
        if found:
            self.report_detected('JW Player in SFWObject')
        else:
            # Look for gorilla-vid style embedding
            found = filter_video(re.findall(r'''(?sx)
                (?:
                    jw_plugins|
                    JWPlayerOptions|
                    jwplayer\s*\(\s*["'][^'"]+["']\s*\)\s*\.setup
                )
                .*?
                ['"]?file['"]?\s*:\s*["\'](.*?)["\']''', webpage))
            if found:
                self.report_detected('JW Player embed')
        if not found:
            # Broaden the search a little bit
            found = filter_video(re.findall(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage))
            if found:
                self.report_detected('video file')
        if not found:
            # Broaden the findall a little bit: JWPlayer JS loader
            found = filter_video(re.findall(
                r'[^A-Za-z0-9]?(?:file|video_url)["\']?:\s*["\'](http(?![^\'"]+\.[0-9]+[\'"])[^\'"]+)["\']', webpage))
            if found:
                self.report_detected('JW Player JS loader')
        if not found:
            # Flow player
            found = filter_video(re.findall(r'''(?xs)
                flowplayer\("[^"]+",\s*
                    \{[^}]+?\}\s*,
                    \s*\{[^}]+? ["']?clip["']?\s*:\s*\{\s*
                        ["']?url["']?\s*:\s*["']([^"']+)["']
            ''', webpage))
            if found:
                self.report_detected('Flow Player')
        if not found:
            # Cinerama player
            found = re.findall(
                r"cinerama\.embedPlayer\(\s*\'[^']+\',\s*'([^']+)'", webpage)
            if found:
                self.report_detected('Cinerama player')
        if not found:
            # Try to find twitter cards info
            # twitter:player:stream should be checked before twitter:player since
            # it is expected to contain a raw stream (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
            found = filter_video(re.findall(
                r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage))
            if found:
                self.report_detected('Twitter card')
        if not found:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them, e.g.: statigr.am
            m_video_type = re.findall(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                found = filter_video(re.findall(r'<meta.*?property="og:(?:video|audio)".*?content="(.*?)"', webpage))
                if found:
                    self.report_detected('Open Graph video info')
        if not found:
            REDIRECT_REGEX = r'[0-9]{,2};\s*(?:URL|url)=\'?([^\'"]+)'
            found = re.search(
                r'(?i)<meta\s+(?=(?:[a-z-]+="[^"]+"\s+)*http-equiv="refresh")'
                rf'(?:[a-z-]+="[^"]+"\s+)*?content="{REDIRECT_REGEX}',
                webpage)
            if not found:
                # Look also in Refresh HTTP header
                refresh_header = urlh and urlh.headers.get('Refresh')
                if refresh_header:
                    found = re.search(REDIRECT_REGEX, refresh_header)
            if found:
                new_url = urllib.parse.urljoin(url, unescapeHTML(found.group(1)))
                if new_url != url:
                    self.report_following_redirect(new_url)
                    return [self.url_result(new_url)]
                else:
                    found = None

        if not found:
            # twitter:player is a https URL to iframe player that may or may not
            # be supported by yt-dlp thus this is checked the very last (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
            embed_url = self._html_search_meta('twitter:player', webpage, default=None)
            if embed_url and embed_url != url:
                self.report_detected('twitter:player iframe')
                return [self.url_result(embed_url)]

        if not found:
            return []

        domain_name = self._search_regex(r'^(?:https?://)?([^/]*)/.*', url, 'video uploader', default=None)

        entries = []
        for video_url in orderedSet(found):
            video_url = video_url.encode().decode('unicode-escape')
            video_url = unescapeHTML(video_url)
            video_url = video_url.replace('\\/', '/')
            video_url = urllib.parse.urljoin(url, video_url)
            video_id = urllib.parse.unquote(os.path.basename(video_url))

            # Sometimes, jwplayer extraction will result in a YouTube URL
            if YoutubeIE.suitable(video_url):
                entries.append(self.url_result(video_url, 'Youtube'))
                continue

            video_id = os.path.splitext(video_id)[0]
            headers = {
                'referer': actual_url,
            }

            entry_info_dict = {
                'id': video_id,
                'uploader': domain_name,
                'title': info_dict['title'],
                'age_limit': info_dict['age_limit'],
                'http_headers': headers,
            }

            if RtmpIE.suitable(video_url):
                entry_info_dict.update({
                    '_type': 'url_transparent',
                    'ie_key': RtmpIE.ie_key(),
                    'url': video_url,
                })
                entries.append(entry_info_dict)
                continue

            ext = determine_ext(video_url)
            if ext == 'smil':
                entry_info_dict = {**self._extract_smil_info(video_url, video_id), **entry_info_dict}
            elif ext == 'xspf':
                return [self._extract_xspf_playlist(video_url, video_id)]
            elif ext == 'm3u8':
                entry_info_dict['formats'], entry_info_dict['subtitles'] = self._extract_m3u8_formats_and_subtitles(video_url, video_id, ext='mp4', headers=headers)
                self._extra_manifest_info(entry_info_dict, video_url)
            elif ext == 'mpd':
                entry_info_dict['formats'], entry_info_dict['subtitles'] = self._extract_mpd_formats_and_subtitles(video_url, video_id, headers=headers)
                self._extra_manifest_info(entry_info_dict, video_url)
            elif ext == 'f4m':
                entry_info_dict['formats'] = self._extract_f4m_formats(video_url, video_id, headers=headers)
            elif re.search(r'(?i)\.(?:ism|smil)/manifest', video_url) and video_url != url:
                # Just matching .ism/manifest is not enough to be reliably sure
                # whether it's actually an ISM manifest or some other streaming
                # manifest since there are various streaming URL formats
                # possible (see [1]) as well as some other shenanigans like
                # .smil/manifest URLs that actually serve an ISM (see [2]) and
                # so on.
                # Thus the most reasonable way to solve this is to delegate
                # to generic extractor in order to look into the contents of
                # the manifest itself.
                # 1. https://azure.microsoft.com/en-us/documentation/articles/media-services-deliver-content-overview/#streaming-url-formats
                # 2. https://svs.itworkscdn.net/lbcivod/smil:itwfcdn/lbci/170976.smil/Manifest
                entry_info_dict = self.url_result(
                    smuggle_url(video_url, {'to_generic': True}),
                    GenericIE.ie_key())
            else:
                entry_info_dict['url'] = video_url

            entries.append(entry_info_dict)

        if len(entries) > 1:
            for num, e in enumerate(entries, start=1):
                # 'url' results don't have a title
                if e.get('title') is not None:
                    e['title'] = '{} ({})'.format(e['title'], num)
        return entries