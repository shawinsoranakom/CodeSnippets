def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        base_url = self.http_scheme() + '//www.youtube.com/'
        webpage_url = base_url + 'watch?v=' + video_id
        ua = traverse_obj(self._INNERTUBE_CLIENTS, (
            'web', 'INNERTUBE_CONTEXT', 'client', 'userAgent'))
        headers = {'User-Agent': ua} if ua else None
        webpage = self._download_webpage(
            webpage_url + '&bpctr=9999999999&has_verified=1', video_id,
            headers=headers, fatal=False)

        player_response = None
        player_url = None
        if webpage:
            player_response = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_PLAYER_RESPONSE_RE,
                video_id, 'initial player response')
        is_live = traverse_obj(player_response, ('videoDetails', 'isLive'))

        fetched_timestamp = None
        if False and not player_response:
            player_response = self._call_api(
                'player', {'videoId': video_id}, video_id)
        if True or not player_response:
            origin = 'https://www.youtube.com'
            pb_context = {'html5Preference': 'HTML5_PREF_WANTS'}
            player_url = self._extract_player_url(webpage)
            ytcfg = self._extract_ytcfg(video_id, webpage or '')
            sts = self._extract_signature_timestamp(video_id, player_url, ytcfg)
            if sts:
                pb_context['signatureTimestamp'] = sts

            auth = self._generate_sapisidhash_header(origin)

            client_names = []
            if auth or self._is_premium_subscriber(player_response):
                client_names = traverse_obj(self._INNERTUBE_CLIENTS, (
                    T(dict_items), lambda _, k_v: k_v[0] == 'web_safari', 0))[:1]
            if not client_names:
                client_names = traverse_obj(self._INNERTUBE_CLIENTS, (
                    T(dict_items), lambda _, k_v: not (
                        k_v[1].get('REQUIRE_PO_TOKEN')
                        or (bool(k_v[1].get('WITH_COOKIES', auth)) ^ bool(auth))
                    ), 0))[:1]
            if 'web' not in client_names:
                # only live HLS webpage links will download: ignore playability
                player_response = filter_dict(
                    player_response or {},
                    lambda k, _: k != 'playabilityStatus')

            headers = {
                'Sec-Fetch-Mode': 'navigate',
                'Origin': origin,
                'X-Goog-Visitor-Id': self._extract_visitor_data(ytcfg) or '',
            }

            if auth is not None:
                headers['Authorization'] = auth
                headers['X-Origin'] = origin

            for client in traverse_obj(self._INNERTUBE_CLIENTS, (client_names, T(dict))):

                query = {
                    'playbackContext': {
                        'contentPlaybackContext': pb_context,
                    },
                    'contentCheckOk': True,
                    'racyCheckOk': True,
                    'context': {
                        'client': merge_dicts(
                            traverse_obj(client, ('INNERTUBE_CONTEXT', 'client')), {
                                'hl': 'en',
                                'timeZone': 'UTC',
                                'utcOffsetMinutes': 0,
                            }),
                    },
                    'videoId': video_id,
                }

                api_headers = merge_dicts(headers, traverse_obj(client, {
                    'X-YouTube-Client-Name': 'INNERTUBE_CONTEXT_CLIENT_NAME',
                    'X-YouTube-Client-Version': (
                        'INNERTUBE_CONTEXT', 'client', 'clientVersion'),
                    'User-Agent': (
                        'INNERTUBE_CONTEXT', 'client', 'userAgent'),
                }) or {})

                api_player_response = self._call_api(
                    'player', query, video_id, fatal=False, headers=api_headers,
                    note=join_nonempty(
                        'Downloading', traverse_obj(query, (
                            'context', 'client', 'clientName')),
                        'API JSON', delim=' '))

                # be sure to find HLS in case of is_live
                hls = traverse_obj(player_response, (
                    'streamingData', 'hlsManifestUrl', T(url_or_none)))
                fetched_timestamp = int(time.time())
                preroll_length_ms = (
                    self._get_preroll_length(api_player_response)
                    or self._get_preroll_length(player_response))
                video_details = merge_dicts(*traverse_obj(
                    (player_response, api_player_response),
                    (Ellipsis, 'videoDetails', T(dict))))
                player_response.update(filter_dict(
                    api_player_response or {}, cndn=lambda k, _: k != 'captions'))
                player_response['videoDetails'] = video_details
                if hls and not traverse_obj(player_response, (
                        'streamingData', 'hlsManifestUrl', T(url_or_none))):
                    player_response['streamingData']['hlsManifestUrl'] = hls

        def is_agegated(playability):
            # playability: dict
            if not playability:
                return False

            if playability.get('desktopLegacyAgeGateReason'):
                return True

            reasons = traverse_obj(playability, (('status', 'reason'),))
            AGE_GATE_REASONS = (
                'confirm your age', 'age-restricted', 'inappropriate',  # reason
                'age_verification_required', 'age_check_required',  # status
            )
            return any(expected in reason for expected in AGE_GATE_REASONS for reason in reasons)

        def get_playability_status(response):
            return try_get(response, lambda x: x['playabilityStatus'], dict) or {}

        playability_status = get_playability_status(player_response)
        if (is_agegated(playability_status)
                and int_or_none(self._downloader.params.get('age_limit'), default=18) >= 18):

            self.report_age_confirmation()

            # Thanks: https://github.com/yt-dlp/yt-dlp/pull/3233
            pb_context = {'html5Preference': 'HTML5_PREF_WANTS'}

            # Use signatureTimestamp if available
            # Thanks https://github.com/ytdl-org/youtube-dl/issues/31034#issuecomment-1160718026
            player_url = self._extract_player_url(webpage)
            ytcfg = self._extract_ytcfg(video_id, webpage)
            sts = self._extract_signature_timestamp(video_id, player_url, ytcfg)
            if sts:
                pb_context['signatureTimestamp'] = sts

            query = {
                'playbackContext': {'contentPlaybackContext': pb_context},
                'contentCheckOk': True,
                'racyCheckOk': True,
                'context': {
                    'client': {'clientName': 'TVHTML5_SIMPLY_EMBEDDED_PLAYER', 'clientVersion': '2.0', 'hl': 'en', 'clientScreen': 'EMBED'},
                    'thirdParty': {'embedUrl': 'https://google.com'},
                },
                'videoId': video_id,
            }
            headers = {
                'X-YouTube-Client-Name': '85',
                'X-YouTube-Client-Version': '2.0',
                'Origin': 'https://www.youtube.com',
            }

            video_info = self._call_api('player', query, video_id, fatal=False, headers=headers)
            age_gate_status = get_playability_status(video_info)
            if age_gate_status.get('status') == 'OK':
                player_response = video_info
                playability_status = age_gate_status

        trailer_video_id = try_get(
            playability_status,
            lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
            compat_str)
        if trailer_video_id:
            return self.url_result(
                trailer_video_id, self.ie_key(), trailer_video_id)

        get_text = lambda x: self._get_text(x) or ''

        search_meta = (
            (lambda x: self._html_search_meta(x, webpage, default=None))
            if webpage else lambda _: None)

        video_details = player_response.get('videoDetails') or {}
        microformat = try_get(
            player_response,
            lambda x: x['microformat']['playerMicroformatRenderer'],
            dict) or {}
        video_title = video_details.get('title') \
            or get_text(microformat.get('title')) \
            or search_meta(['og:title', 'twitter:title', 'title'])
        video_description = video_details.get('shortDescription')

        if not smuggled_data.get('force_singlefeed', False):
            if not self._downloader.params.get('noplaylist'):
                multifeed_metadata_list = try_get(
                    player_response,
                    lambda x: x['multicamera']['playerLegacyMulticameraRenderer']['metadataList'],
                    compat_str)
                if multifeed_metadata_list:
                    entries = []
                    feed_ids = []
                    for feed in multifeed_metadata_list.split(','):
                        # Unquote should take place before split on comma (,) since textual
                        # fields may contain comma as well (see
                        # https://github.com/ytdl-org/youtube-dl/issues/8536)
                        feed_data = compat_parse_qs(
                            compat_urllib_parse_unquote_plus(feed))

                        def feed_entry(name):
                            return try_get(
                                feed_data, lambda x: x[name][0], compat_str)

                        feed_id = feed_entry('id')
                        if not feed_id:
                            continue
                        feed_title = feed_entry('title')
                        title = video_title
                        if feed_title:
                            title += ' (%s)' % feed_title
                        entries.append({
                            '_type': 'url_transparent',
                            'ie_key': 'Youtube',
                            'url': smuggle_url(
                                base_url + 'watch?v=' + feed_data['id'][0],
                                {'force_singlefeed': True}),
                            'title': title,
                        })
                        feed_ids.append(feed_id)
                    self.to_screen(
                        'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
                        % (', '.join(feed_ids), video_id))
                    return self.playlist_result(
                        entries, video_id, video_title, video_description)
            else:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        if not player_url:
            player_url = self._extract_player_url(webpage)

        formats = []
        itags = collections.defaultdict(set)
        itag_qualities = {}
        q = qualities(['tiny', 'small', 'medium', 'large', 'hd720', 'hd1080', 'hd1440', 'hd2160', 'hd2880', 'highres'])
        CHUNK_SIZE = 10 << 20
        is_live = video_details.get('isLive')

        streaming_data = player_response.get('streamingData') or {}
        streaming_formats = streaming_data.get('formats') or []
        streaming_formats.extend(streaming_data.get('adaptiveFormats') or [])

        def build_fragments(f):
            return LazyList({
                'url': update_url_query(f['url'], {
                    'range': '{0}-{1}'.format(range_start, min(range_start + CHUNK_SIZE - 1, f['filesize'])),
                }),
            } for range_start in range(0, f['filesize'], CHUNK_SIZE))

        lower = lambda s: s.lower()

        if is_live:
            fetched_timestamp = None
        elif fetched_timestamp is not None:
            # Handle preroll waiting period
            preroll_sleep = self.get_param('youtube_preroll_sleep')
            preroll_sleep = min(6, int_or_none(preroll_sleep, default=preroll_length_ms / 1000))
            fetched_timestamp += preroll_sleep

        for fmt in streaming_formats:
            if fmt.get('targetDurationSec'):
                continue

            itag = str_or_none(fmt.get('itag'))
            audio_track = traverse_obj(fmt, ('audioTrack', T(dict))) or {}

            quality = traverse_obj(fmt, ((
                # The 3gp format (17) in android client has a quality of "small",
                # but is actually worse than other formats
                T(lambda _: 'tiny' if itag == 17 else None),
                ('quality', T(lambda q: q if q and q != 'tiny' else None)),
                ('audioQuality', T(lower)),
                'quality'), T(txt_or_none)), get_all=False)
            if quality and itag:
                itag_qualities[itag] = quality
            # FORMAT_STREAM_TYPE_OTF(otf=1) requires downloading the init fragment
            # (adding `&sq=0` to the URL) and parsing emsg box to determine the
            # number of fragments that would subsequently be requested with (`&sq=N`)
            if fmt.get('type') == 'FORMAT_STREAM_TYPE_OTF':
                continue

            fmt_url = fmt.get('url')
            if not fmt_url:
                sc = compat_parse_qs(fmt.get('signatureCipher'))
                fmt_url = traverse_obj(sc, ('url', -1, T(url_or_none)))
                encrypted_sig = traverse_obj(sc, ('s', -1))
                if not (fmt_url and encrypted_sig):
                    continue
                player_url = player_url or self._extract_player_url(webpage)
                if not player_url:
                    continue
                try:
                    fmt_url = update_url_query(fmt_url, {
                        traverse_obj(sc, ('sp', -1)) or 'signature':
                            [self._decrypt_signature(encrypted_sig, video_id, player_url)],
                    })
                except ExtractorError as e:
                    self.report_warning('Signature extraction failed: Some formats may be missing',
                                        video_id=video_id, only_once=True)
                    self.write_debug(error_to_compat_str(e), only_once=True)
                    continue

            if parse_qs(fmt_url).get('n'):
                # this and (we assume) all the formats here are n-scrambled
                break

            language_preference = (
                10 if audio_track.get('audioIsDefault')
                else -10 if 'descriptive' in (traverse_obj(audio_track, ('displayName', T(lower))) or '')
                else -1)
            name = (
                traverse_obj(fmt, ('qualityLabel', T(txt_or_none)))
                or quality.replace('audio_quality_', ''))
            dct = {
                'format_id': join_nonempty(itag, fmt.get('isDrc') and 'drc'),
                'url': fmt_url,
                # Format 22 is likely to be damaged: see https://github.com/yt-dlp/yt-dlp/issues/3372
                'source_preference': ((-5 if itag == '22' else -1)
                                      + (100 if 'Premium' in name else 0)),
                'quality': q(quality),
                'language': join_nonempty(audio_track.get('id', '').split('.')[0],
                                          'desc' if language_preference < -1 else '') or None,
                'language_preference': language_preference,
                # Strictly de-prioritize 3gp formats
                'preference': -2 if itag == '17' else None,
            }
            if itag:
                itags[itag].add(('https', dct.get('language')))
            self._unthrottle_format_urls(video_id, player_url, dct)
            dct.update(traverse_obj(fmt, {
                'asr': ('audioSampleRate', T(int_or_none)),
                'filesize': ('contentLength', T(int_or_none)),
                'format_note': ('qualityLabel', T(lambda x: x or quality)),
                # for some formats, fps is wrongly returned as 1
                'fps': ('fps', T(int_or_none), T(lambda f: f if f > 1 else None)),
                'audio_channels': ('audioChannels', T(int_or_none)),
                'height': ('height', T(int_or_none)),
                'has_drm': ('drmFamilies', T(bool)),
                'tbr': (('averageBitrate', 'bitrate'), T(lambda t: float_or_none(t, 1000))),
                'width': ('width', T(int_or_none)),
                '_duration_ms': ('approxDurationMs', T(int_or_none)),
            }, get_all=False))
            mime_mobj = re.match(
                r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', fmt.get('mimeType') or '')
            if mime_mobj:
                dct['ext'] = mimetype2ext(mime_mobj.group(1))
                dct.update(parse_codecs(mime_mobj.group(2)))
            single_stream = 'none' in (dct.get(c) for c in ('acodec', 'vcodec'))
            if single_stream and dct.get('ext'):
                dct['container'] = dct['ext'] + '_dash'
            if single_stream or itag == '17':
                # avoid Youtube throttling
                dct.update({
                    'protocol': 'http_dash_segments',
                    'fragments': build_fragments(dct),
                } if dct['filesize'] else {
                    'downloader_options': {'http_chunk_size': CHUNK_SIZE},  # No longer useful?
                })

            if fetched_timestamp:
                dct['available_at'] = fetched_timestamp

            formats.append(dct)

        def process_manifest_format(f, proto, client_name, itag, all_formats=False):
            key = (proto, f.get('language'))
            if not all_formats and key in itags[itag]:
                return False
            itags[itag].add(key)

            if itag:
                f['format_id'] = (
                    '{0}-{1}'.format(itag, proto)
                    if all_formats or any(p != proto for p, _ in itags[itag])
                    else itag)

            if f.get('source_preference') is None:
                f['source_preference'] = -1

            # Deprioritize since its pre-merged m3u8 formats may have lower quality audio streams
            if client_name == 'web_safari' and proto == 'hls' and not is_live:
                f['source_preference'] -= 1

            if itag in ('616', '235'):
                f['format_note'] = join_nonempty(f.get('format_note'), 'Premium', delim=' ')
                f['source_preference'] += 100

            f['quality'] = q(traverse_obj(f, (
                'format_id', T(lambda s: itag_qualities[s.split('-')[0]])), default=-1))
            if try_call(lambda: f['fps'] <= 1):
                del f['fps']

            if proto == 'hls' and f.get('has_drm'):
                f['has_drm'] = 'maybe'
                f['source_preference'] -= 5
            return True

        hls_manifest_url = streaming_data.get('hlsManifestUrl')
        if hls_manifest_url:
            formats.extend(
                f for f in self._extract_m3u8_formats(
                    hls_manifest_url, video_id, 'mp4',
                    entry_protocol='m3u8_native', live=is_live, fatal=False)
                if process_manifest_format(
                    f, 'hls', None, self._search_regex(
                        r'/itag/(\d+)', f['url'], 'itag', default=None)))

        if self.get_param('youtube_include_dash_manifest', True):
            dash_manifest_url = streaming_data.get('dashManifestUrl')
            if dash_manifest_url:
                for f in self._extract_mpd_formats(
                        dash_manifest_url, video_id, fatal=False):
                    if process_manifest_format(
                            f, 'dash', None, f['format_id']):
                        f['filesize'] = traverse_obj(f, (
                            ('fragment_base_url', 'url'), T(lambda u: self._search_regex(
                                r'/clen/(\d+)', u, 'file size', default=None)),
                            T(int_or_none)), get_all=False)
                        formats.append(f)

        playable_formats = [f for f in formats if not f.get('has_drm')]
        if formats:
            if not playable_formats:
                # If there are no formats that definitely don't have DRM, all have DRM
                self.report_drm(video_id)
            formats[:] = playable_formats
        else:
            if streaming_data.get('licenseInfos'):
                raise ExtractorError(
                    'This video is DRM protected.', expected=True)
            pemr = try_get(
                playability_status,
                lambda x: x['errorScreen']['playerErrorMessageRenderer'],
                dict) or {}
            reason = get_text(pemr.get('reason')) or playability_status.get('reason') or ''
            subreason = pemr.get('subreason')
            if subreason:
                subreason = clean_html(get_text(subreason))
                if subreason.startswith('The uploader has not made this video available in your country'):
                    countries = microformat.get('availableCountries')
                    if not countries:
                        regions_allowed = search_meta('regionsAllowed')
                        countries = regions_allowed.split(',') if regions_allowed else None
                    self.raise_geo_restricted(
                        subreason, countries)
                reason += '\n' + subreason

            if reason:
                if 'sign in' in reason.lower():
                    self.raise_login_required(remove_end(reason, 'This helps protect our community. Learn more'))
                elif traverse_obj(playability_status, ('errorScreen', 'playerCaptchaViewModel', T(dict))):
                    reason += '. YouTube is requiring a captcha challenge before playback'
                raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        keywords = video_details.get('keywords') or []
        if not keywords and webpage:
            keywords = [
                unescapeHTML(m.group('content'))
                for m in re.finditer(self._meta_regex('og:video:tag'), webpage)]
        for keyword in keywords:
            if keyword.startswith('yt:stretch='):
                mobj = re.search(r'(\d+)\s*:\s*(\d+)', keyword)
                if mobj:
                    # NB: float is intentional for forcing float division
                    w, h = (float(v) for v in mobj.groups())
                    if w > 0 and h > 0:
                        ratio = w / h
                        for f in formats:
                            if f.get('vcodec') != 'none':
                                f['stretched_ratio'] = ratio
                        break

        thumbnails = []
        for container in (video_details, microformat):
            for thumbnail in try_get(
                    container,
                    lambda x: x['thumbnail']['thumbnails'], list) or []:
                thumbnail_url = url_or_none(thumbnail.get('url'))
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'height': int_or_none(thumbnail.get('height')),
                    'url': update_url(thumbnail_url, query=None, fragment=None),
                    'width': int_or_none(thumbnail.get('width')),
                })
            if thumbnails:
                break
        else:
            thumbnail = search_meta(['og:image', 'twitter:image'])
            if thumbnail:
                thumbnails = [{'url': thumbnail}]

        category = microformat.get('category') or search_meta('genre')
        channel_id = self._extract_channel_id(
            webpage, videodetails=video_details, metadata=microformat)
        duration = int_or_none(
            video_details.get('lengthSeconds')
            or microformat.get('lengthSeconds')) \
            or parse_duration(search_meta('duration'))

        for f in formats:
            # Some formats may have much smaller duration than others (possibly damaged during encoding)
            # but avoid false positives with small duration differences.
            # Ref: https://github.com/yt-dlp/yt-dlp/issues/2823
            if try_call(lambda x: float(x.pop('_duration_ms')) / duration < 500, args=(f,)):
                self.report_warning(
                    '{0}: Some possibly damaged formats will be deprioritized'.format(video_id), only_once=True)
                # Strictly de-prioritize damaged formats
                f['preference'] = -10

        owner_profile_url = self._yt_urljoin(self._extract_author_var(
            webpage, 'url', videodetails=video_details, metadata=microformat))

        uploader = self._extract_author_var(
            webpage, 'name', videodetails=video_details, metadata=microformat)

        info = {
            'id': video_id,
            'title': self._live_title(video_title) if is_live else video_title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': video_description,
            'upload_date': unified_strdate(
                microformat.get('uploadDate')
                or search_meta('uploadDate')),
            'uploader': uploader,
            'channel_id': channel_id,
            'duration': duration,
            'view_count': int_or_none(
                video_details.get('viewCount')
                or microformat.get('viewCount')
                or search_meta('interactionCount')),
            'average_rating': float_or_none(video_details.get('averageRating')),
            'age_limit': 18 if (
                microformat.get('isFamilySafe') is False
                or search_meta('isFamilyFriendly') == 'false'
                or search_meta('og:restrictions:age') == '18+') else 0,
            'webpage_url': webpage_url,
            'categories': [category] if category else None,
            'tags': keywords,
            'is_live': is_live,
        }

        pctr = traverse_obj(
            (player_response, api_player_response),
            (Ellipsis, 'captions', 'playerCaptionsTracklistRenderer', T(dict)))
        if pctr:
            def process_language(container, base_url, lang_code, query):
                lang_subs = []
                for fmt in self._SUBTITLE_FORMATS:
                    query.update({
                        'fmt': fmt,
                        # xosf=1 causes undesirable text position data for vtt, json3 & srv* subtitles
                        # See: https://github.com/yt-dlp/yt-dlp/issues/13654
                        'xosf': [],
                    })
                    lang_subs.append({
                        'ext': fmt,
                        'url': update_url_query(base_url, query),
                    })
                container[lang_code] = lang_subs

            def process_subtitles():
                subtitles = {}
                for caption_track in traverse_obj(pctr, (
                        Ellipsis, 'captionTracks', lambda _, v: (
                            v.get('baseUrl') and v.get('languageCode')))):
                    base_url = self._yt_urljoin(caption_track['baseUrl'])
                    if not base_url:
                        continue
                    lang_code = caption_track['languageCode']
                    if caption_track.get('kind') != 'asr':
                        process_language(
                            subtitles, base_url, lang_code, {})
                        continue
                    automatic_captions = {}
                    process_language(
                        automatic_captions, base_url, lang_code, {})
                    for translation_language in traverse_obj(pctr, (
                            Ellipsis, 'translationLanguages', lambda _, v: v.get('languageCode'))):
                        translation_language_code = translation_language['languageCode']
                        process_language(
                            automatic_captions, base_url, translation_language_code,
                            {'tlang': translation_language_code})
                    info['automatic_captions'] = automatic_captions
                info['subtitles'] = subtitles

            process_subtitles()

        parsed_url = compat_urllib_parse_urlparse(url)
        for component in (parsed_url.fragment, parsed_url.query):
            query = compat_parse_qs(component)
            for k, v in query.items():
                for d_k, s_ks in [('start', ('start', 't')), ('end', ('end',))]:
                    d_k += '_time'
                    if d_k not in info and k in s_ks:
                        info[d_k] = parse_duration(v[0])

        if video_description:
            # Youtube Music Auto-generated description
            mobj = re.search(r'(?s)(?P<track>[^·\n]+)·(?P<artist>[^\n]+)\n+(?P<album>[^\n]+)(?:.+?℗\s*(?P<release_year>\d{4})(?!\d))?(?:.+?Released on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?(.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+))?.+\nAuto-generated by YouTube\.\s*$', video_description)
            if mobj:
                release_year = mobj.group('release_year')
                release_date = mobj.group('release_date')
                if release_date:
                    release_date = release_date.replace('-', '')
                    if not release_year:
                        release_year = release_date[:4]
                info.update({
                    'album': mobj.group('album'.strip()),
                    'artist': mobj.group('clean_artist') or ', '.join(a.strip() for a in mobj.group('artist').split('·')),
                    'track': mobj.group('track').strip(),
                    'release_date': release_date,
                    'release_year': int_or_none(release_year),
                })

        initial_data = None
        if webpage:
            initial_data = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_DATA_RE, video_id,
                'yt initial data')
        if not initial_data:
            initial_data = self._call_api(
                'next', {'videoId': video_id}, video_id, fatal=False)

        initial_sdcr = None
        if initial_data:
            chapters = self._extract_chapters_from_json(
                initial_data, video_id, duration)
            if not chapters:
                def chapter_time(mmlir):
                    return parse_duration(
                        get_text(mmlir.get('timeDescription')))

                for markers in traverse_obj(initial_data, (
                        'engagementPanels', Ellipsis, 'engagementPanelSectionListRenderer',
                        'content', 'macroMarkersListRenderer', 'contents', T(list))):

                    chapters = []
                    for next_num, content in enumerate(markers, start=1):
                        mmlir = content.get('macroMarkersListItemRenderer') or {}
                        start_time = chapter_time(mmlir)
                        end_time = (traverse_obj(markers, (
                            next_num, 'macroMarkersListItemRenderer', T(chapter_time)))
                            if next_num < len(markers) else duration)
                        if start_time is None or end_time is None:
                            continue
                        chapters.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'title': get_text(mmlir.get('title')),
                        })
                    if chapters:
                        break
            if chapters:
                info['chapters'] = chapters

            contents = try_get(
                initial_data,
                lambda x: x['contents']['twoColumnWatchNextResults']['results']['results']['contents'],
                list) or []
            if not info['channel_id']:
                channel_id = self._extract_channel_id('', renderers=contents)
            if not info['uploader']:
                info['uploader'] = self._extract_author_var('', 'name', renderers=contents)
            if not owner_profile_url:
                owner_profile_url = self._yt_urljoin(self._extract_author_var('', 'url', renderers=contents))

            for content in contents:
                vpir = content.get('videoPrimaryInfoRenderer')
                if vpir:
                    stl = vpir.get('superTitleLink')
                    if stl:
                        stl = get_text(stl)
                        if try_get(
                                vpir,
                                lambda x: x['superTitleIcon']['iconType']) == 'LOCATION_PIN':
                            info['location'] = stl
                        else:
                            # •? doesn't match, but [•]? does; \xa0 = non-breaking space
                            mobj = re.search(r'([^\xa0\s].*?)[\xa0\s]*S(\d+)[\xa0\s]*[•]?[\xa0\s]*E(\d+)', stl)
                            if mobj:
                                info.update({
                                    'series': mobj.group(1),
                                    'season_number': int(mobj.group(2)),
                                    'episode_number': int(mobj.group(3)),
                                })
                    for tlb in (try_get(
                            vpir,
                            lambda x: x['videoActions']['menuRenderer']['topLevelButtons'],
                            list) or []):
                        tbr = traverse_obj(tlb, ('segmentedLikeDislikeButtonRenderer', 'likeButton', 'toggleButtonRenderer'), 'toggleButtonRenderer') or {}
                        for getter, regex in [(
                                lambda x: x['defaultText']['accessibility']['accessibilityData'],
                                r'(?P<count>[\d,]+)\s*(?P<type>(?:dis)?like)'), ([
                                    lambda x: x['accessibility'],
                                    lambda x: x['accessibilityData']['accessibilityData'],
                                ], r'(?P<type>(?:dis)?like) this video along with (?P<count>[\d,]+) other people')]:
                            label = (try_get(tbr, getter, dict) or {}).get('label')
                            if label:
                                mobj = re.match(regex, label)
                                if mobj:
                                    info[mobj.group('type') + '_count'] = str_to_int(mobj.group('count'))
                                    break
                    sbr_tooltip = try_get(
                        vpir, lambda x: x['sentimentBar']['sentimentBarRenderer']['tooltip'])
                    if sbr_tooltip:
                        # however dislike_count was hidden by YT, as if there could ever be dislikable content on YT
                        like_count, dislike_count = sbr_tooltip.split(' / ')
                        info.update({
                            'like_count': str_to_int(like_count),
                            'dislike_count': str_to_int(dislike_count),
                        })
                    else:
                        info['like_count'] = traverse_obj(vpir, (
                            'videoActions', 'menuRenderer', 'topLevelButtons', Ellipsis,
                            'segmentedLikeDislikeButtonViewModel', 'likeButtonViewModel', 'likeButtonViewModel',
                            'toggleButtonViewModel', 'toggleButtonViewModel', 'defaultButtonViewModel',
                            'buttonViewModel', (('title', ('accessibilityText', T(lambda s: s.split()), Ellipsis))), T(parse_count)),
                            get_all=False)

                vsir = content.get('videoSecondaryInfoRenderer')
                if vsir:
                    rows = try_get(
                        vsir,
                        lambda x: x['metadataRowContainer']['metadataRowContainerRenderer']['rows'],
                        list) or []
                    multiple_songs = False
                    for row in rows:
                        if try_get(row, lambda x: x['metadataRowRenderer']['hasDividerLine']) is True:
                            multiple_songs = True
                            break
                    for row in rows:
                        mrr = row.get('metadataRowRenderer') or {}
                        mrr_title = mrr.get('title')
                        if not mrr_title:
                            continue
                        mrr_title = get_text(mrr['title'])
                        mrr_contents_text = get_text(mrr['contents'][0])
                        if mrr_title == 'License':
                            info['license'] = mrr_contents_text
                        elif not multiple_songs:
                            if mrr_title == 'Album':
                                info['album'] = mrr_contents_text
                            elif mrr_title == 'Artist':
                                info['artist'] = mrr_contents_text
                            elif mrr_title == 'Song':
                                info['track'] = mrr_contents_text

            # this is not extraction but spelunking!
            initial_sdcr = traverse_obj(initial_data, (
                'engagementPanels', Ellipsis, 'engagementPanelSectionListRenderer',
                'content', 'structuredDescriptionContentRenderer', T(dict)),
                get_all=False)
            carousel_lockups = traverse_obj(initial_sdcr, (
                'items', Ellipsis, 'videoDescriptionMusicSectionRenderer',
                'carouselLockups', Ellipsis, T(dict))) or []
            # try to reproduce logic from metadataRowContainerRenderer above (if it still is)
            fields = (('ALBUM', 'album'), ('ARTIST', 'artist'), ('SONG', 'track'), ('LICENSES', 'license'))
            # multiple_songs ?
            if len(carousel_lockups) > 1:
                fields = fields[-1:]
            for info_row in traverse_obj(
                    carousel_lockups,
                    (0, 'carouselLockupRenderer', 'infoRows', Ellipsis, 'infoRowRenderer'),
                    expected_type=dict):
                row_title = traverse_obj(info_row, ('title', 'simpleText'))
                row_text = traverse_obj(info_row, 'defaultMetadata', 'expandedMetadata', expected_type=get_text)
                if not row_text:
                    continue
                for name, field in fields:
                    if name == row_title and not info.get(field):
                        info[field] = row_text

        for s_k, d_k in [('artist', 'creator'), ('track', 'alt_title')]:
            v = info.get(s_k)
            if v:
                info[d_k] = v

        self.mark_watched(video_id, player_response)

        # Fallbacks for missing metadata
        if initial_sdcr:
            if info.get('description') is None:
                info['description'] = traverse_obj(initial_sdcr, (
                    'items', Ellipsis, 'expandableVideoDescriptionBodyRenderer',
                    'attributedDescriptionBodyText', 'content', T(compat_str)),
                    get_all=False)
            # videoDescriptionHeaderRenderer also has publishDate/channel/handle/ucid, but not needed
            if info.get('title') is None:
                info['title'] = traverse_obj(
                    (initial_sdcr, initial_data),
                    (0, 'items', Ellipsis, 'videoDescriptionHeaderRenderer', T(dict)),
                    (1, 'playerOverlays', 'playerOverlayRenderer', 'videoDetails',
                     'playerOverlayVideoDetailsRenderer', T(dict)),
                    expected_type=lambda x: self._get_text(x, 'title'),
                    get_all=False)

        return merge_dicts(
            info, {
                'uploader_id': self._extract_uploader_id(owner_profile_url),
                'uploader_url': owner_profile_url,
                'channel_id': channel_id,
                'channel_url': channel_id and self._yt_urljoin('/channel/' + channel_id),
                'channel': info['uploader'],
            })