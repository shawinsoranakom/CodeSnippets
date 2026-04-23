def _extract_formats_and_subtitles(self, video_id, player_responses, player_url, live_status, duration):
        CHUNK_SIZE = 10 << 20
        ORIGINAL_LANG_VALUE = 10
        DEFAULT_LANG_VALUE = 5
        language_map = {
            ORIGINAL_LANG_VALUE: None,
            DEFAULT_LANG_VALUE: None,
        }
        itags, stream_ids = collections.defaultdict(set), []
        itag_qualities, res_qualities = {}, {0: None}
        subtitles = {}
        q = qualities([
            # Normally tiny is the smallest video-only formats. But
            # audio-only formats with unknown quality may get tagged as tiny
            'tiny',
            'audio_quality_ultralow', 'audio_quality_low', 'audio_quality_medium', 'audio_quality_high',  # Audio only formats
            'small', 'medium', 'large', 'hd720', 'hd1080', 'hd1440', 'hd2160', 'hd2880', 'highres',
        ])
        skip_player_js = 'js' in self._configuration_arg('player_skip')
        format_types = self._configuration_arg('formats')
        skip_bad_formats = 'incomplete' not in format_types
        all_formats = 'duplicate' in format_types
        if self._configuration_arg('include_duplicate_formats'):
            all_formats = True
            self._downloader.deprecated_feature('[youtube] include_duplicate_formats extractor argument is deprecated. '
                                                'Use formats=duplicate extractor argument instead')

        def is_super_resolution(f_url):
            return '1' in traverse_obj(f_url, ({parse_qs}, 'xtags', ..., {urllib.parse.parse_qs}, 'sr', ...))

        def solve_sig(s, spec):
            return ''.join(s[i] for i in spec)

        def build_fragments(f):
            return LazyList({
                'url': update_url_query(f['url'], {
                    'range': f'{range_start}-{min(range_start + CHUNK_SIZE - 1, f["filesize"])}',
                }),
            } for range_start in range(0, f['filesize'], CHUNK_SIZE))

        def gvs_pot_required(policy, is_premium_subscriber, has_player_token):
            return (
                policy.required
                and not (policy.not_required_with_player_token and has_player_token)
                and not (policy.not_required_for_premium and is_premium_subscriber))

        # save pots per client to avoid fetching again
        gvs_pots = {}

        def get_language_code_and_preference(fmt_stream):
            audio_track = fmt_stream.get('audioTrack') or {}
            display_name = audio_track.get('displayName') or ''
            language_code = audio_track.get('id', '').split('.')[0] or None
            if 'descriptive' in display_name.lower():
                return join_nonempty(language_code, 'desc'), -10
            if 'original' in display_name.lower():
                if language_code and not language_map.get(ORIGINAL_LANG_VALUE):
                    language_map[ORIGINAL_LANG_VALUE] = language_code
                return language_code, ORIGINAL_LANG_VALUE
            if audio_track.get('audioIsDefault'):
                if language_code and not language_map.get(DEFAULT_LANG_VALUE):
                    language_map[DEFAULT_LANG_VALUE] = language_code
                return language_code, DEFAULT_LANG_VALUE
            return language_code, -1

        def get_manifest_n_challenge(manifest_url):
            if not url_or_none(manifest_url):
                return None
            # Same pattern that the player JS uses to read/replace the n challenge value
            return self._search_regex(
                r'/n/([^/]+)/', urllib.parse.urlparse(manifest_url).path,
                'n challenge', default=None)

        n_challenges = set()
        s_challenges = set()

        def solve_js_challenges():
            # Solve all n/sig challenges in bulk and store the results in self._player_cache
            challenge_requests = []
            if n_challenges:
                challenge_requests.append(JsChallengeRequest(
                    type=JsChallengeType.N,
                    video_id=video_id,
                    input=NChallengeInput(challenges=list(n_challenges), player_url=player_url)))
            if s_challenges:
                cached_sigfuncs = set()
                for spec_id in s_challenges:
                    if self._load_player_data_from_cache('sigfuncs', player_url, spec_id, use_disk_cache=True):
                        cached_sigfuncs.add(spec_id)
                s_challenges.difference_update(cached_sigfuncs)

                challenge_requests.append(JsChallengeRequest(
                    type=JsChallengeType.SIG,
                    video_id=video_id,
                    input=SigChallengeInput(
                        challenges=[''.join(map(chr, range(spec_id))) for spec_id in s_challenges],
                        player_url=player_url)))

            if challenge_requests:
                for _challenge_request, challenge_response in self._jsc_director.bulk_solve(challenge_requests):
                    if challenge_response.type == JsChallengeType.SIG:
                        for challenge, result in challenge_response.output.results.items():
                            spec_id = len(challenge)
                            self._store_player_data_to_cache(
                                [ord(c) for c in result], 'sigfuncs',
                                player_url, spec_id, use_disk_cache=True)
                            if spec_id in s_challenges:
                                s_challenges.remove(spec_id)

                    elif challenge_response.type == JsChallengeType.N:
                        for challenge, result in challenge_response.output.results.items():
                            self._store_player_data_to_cache(result, 'n', player_url, challenge)
                            if challenge in n_challenges:
                                n_challenges.remove(challenge)

                # Raise warning if any challenge requests remain
                # Depending on type of challenge request
                help_message = (
                    'Ensure you have a supported JavaScript runtime and '
                    'challenge solver script distribution installed. '
                    'Review any warnings presented before this message. '
                    f'For more details, refer to  {_EJS_WIKI_URL}')
                if s_challenges:
                    self.report_warning(
                        f'Signature solving failed: Some formats may be missing. {help_message}',
                        video_id=video_id, only_once=True)
                if n_challenges:
                    self.report_warning(
                        f'n challenge solving failed: Some formats may be missing. {help_message}',
                        video_id=video_id, only_once=True)

                # Clear challenge sets so that any subsequent call of this function is a no-op
                s_challenges.clear()
                n_challenges.clear()

        # 1st pass to collect all n/sig challenges so they can later be solved at once in bulk
        for streaming_data in traverse_obj(player_responses, (..., 'streamingData', {dict})):
            # HTTPS formats
            for fmt_stream in traverse_obj(streaming_data, (('formats', 'adaptiveFormats'), ..., {dict})):
                fmt_url = fmt_stream.get('url')
                s_challenge = None
                if not fmt_url:
                    sc = urllib.parse.parse_qs(fmt_stream.get('signatureCipher'))
                    fmt_url = traverse_obj(sc, ('url', 0, {url_or_none}))
                    s_challenge = traverse_obj(sc, ('s', 0))

                if s_challenge:
                    s_challenges.add(len(s_challenge))

                if n_challenge := traverse_obj(fmt_url, ({parse_qs}, 'n', 0)):
                    n_challenges.add(n_challenge)

            # Manifest formats
            n_challenges.update(traverse_obj(
                streaming_data, (('hlsManifestUrl', 'dashManifestUrl'), {get_manifest_n_challenge})))

        # Final pass to extract formats and solve n/sig challenges as needed
        for pr in player_responses:
            streaming_data = traverse_obj(pr, 'streamingData')
            if not streaming_data:
                continue
            fetch_po_token_func = streaming_data[STREAMING_DATA_FETCH_GVS_PO_TOKEN]
            is_premium_subscriber = streaming_data[STREAMING_DATA_IS_PREMIUM_SUBSCRIBER]
            player_token_provided = streaming_data[STREAMING_DATA_PLAYER_TOKEN_PROVIDED]
            client_name = streaming_data.get(STREAMING_DATA_CLIENT_NAME)
            available_at = streaming_data[STREAMING_DATA_AVAILABLE_AT_TIMESTAMP]
            streaming_formats = traverse_obj(streaming_data, (('formats', 'adaptiveFormats'), ...))

            def get_stream_id(fmt_stream):
                return str_or_none(fmt_stream.get('itag')), traverse_obj(fmt_stream, 'audioTrack', 'id'), fmt_stream.get('isDrc')

            def process_format_stream(fmt_stream, proto, missing_pot, super_resolution=False):
                itag = str_or_none(fmt_stream.get('itag'))
                audio_track = fmt_stream.get('audioTrack') or {}
                quality = fmt_stream.get('quality')
                height = int_or_none(fmt_stream.get('height'))
                if quality == 'tiny' or not quality:
                    quality = fmt_stream.get('audioQuality', '').lower() or quality
                # The 3gp format (17) in android client has a quality of "small",
                # but is actually worse than other formats
                if itag == '17':
                    quality = 'tiny'
                if quality:
                    if itag:
                        itag_qualities[itag] = quality
                    if height:
                        res_qualities[height] = quality

                language_code, language_preference = get_language_code_and_preference(fmt_stream)

                has_drm = bool(fmt_stream.get('drmFamilies'))

                if has_drm:
                    msg = f'Some {client_name} client {proto} formats have been skipped as they are DRM protected. '
                    if client_name == 'tv':
                        msg += (
                            f'{"Your account" if self.is_authenticated else "The current session"} may have '
                            f'an experiment that applies DRM to all videos on the tv client. '
                            f'See  https://github.com/yt-dlp/yt-dlp/issues/12563  for more details.'
                        )
                    self.report_warning(msg, video_id, only_once=True)

                tbr = float_or_none(fmt_stream.get('averageBitrate') or fmt_stream.get('bitrate'), 1000)
                format_duration = traverse_obj(fmt_stream, ('approxDurationMs', {float_or_none(scale=1000)}))
                # Some formats may have much smaller duration than others (possibly damaged during encoding)
                # E.g. 2-nOtRESiUc Ref: https://github.com/yt-dlp/yt-dlp/issues/2823
                # Make sure to avoid false positives with small duration differences.
                # E.g. __2ABJjxzNo, ySuUZEjARPY
                is_damaged = try_call(lambda: format_duration < duration // 2)
                if is_damaged:
                    self.report_warning(
                        f'Some {client_name} client {proto} formats are possibly damaged. They will be deprioritized', video_id, only_once=True)

                if missing_pot and 'missing_pot' not in self._configuration_arg('formats'):
                    self._report_pot_format_skipped(video_id, client_name, proto)
                    return None

                name = fmt_stream.get('qualityLabel') or quality.replace('audio_quality_', '') or ''
                fps = int_or_none(fmt_stream.get('fps')) or 0
                dct = {
                    'asr': int_or_none(fmt_stream.get('audioSampleRate')),
                    'filesize': int_or_none(fmt_stream.get('contentLength')),
                    'format_id': join_nonempty(itag, (
                        'drc' if fmt_stream.get('isDrc')
                        else 'sr' if super_resolution
                        else None)),
                    'format_note': join_nonempty(
                        join_nonempty(audio_track.get('displayName'), audio_track.get('audioIsDefault') and '(default)', delim=' '),
                        name, fmt_stream.get('isDrc') and 'DRC', super_resolution and 'AI-upscaled',
                        try_get(fmt_stream, lambda x: x['projectionType'].replace('RECTANGULAR', '').lower()),
                        try_get(fmt_stream, lambda x: x['spatialAudioType'].replace('SPATIAL_AUDIO_TYPE_', '').lower()),
                        is_damaged and 'DAMAGED', missing_pot and 'MISSING POT',
                        (self.get_param('verbose') or all_formats) and short_client_name(client_name),
                        delim=', '),
                    # Format 22 is likely to be damaged. See https://github.com/yt-dlp/yt-dlp/issues/3372
                    'source_preference': (-5 if itag == '22' else -1) + (100 if 'Premium' in name else 0),
                    'fps': fps if fps > 1 else None,  # For some formats, fps is wrongly returned as 1
                    'audio_channels': fmt_stream.get('audioChannels'),
                    'height': height,
                    'quality': q(quality) - bool(fmt_stream.get('isDrc')) / 2,
                    'has_drm': has_drm,
                    'tbr': tbr,
                    'filesize_approx': filesize_from_tbr(tbr, format_duration),
                    'width': int_or_none(fmt_stream.get('width')),
                    'language': language_code,
                    'language_preference': language_preference,
                    # Strictly de-prioritize damaged and 3gp formats
                    'preference': -10 if is_damaged else -2 if itag == '17' else None,
                }
                mime_mobj = re.match(
                    r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', fmt_stream.get('mimeType') or '')
                if mime_mobj:
                    dct['ext'] = mimetype2ext(mime_mobj.group(1))
                    dct.update(parse_codecs(mime_mobj.group(2)))

                single_stream = 'none' in (dct.get('acodec'), dct.get('vcodec'))
                if single_stream and dct.get('ext'):
                    dct['container'] = dct['ext'] + '_dash'

                return dct

            def process_https_formats():
                proto = 'https'
                https_fmts = []

                for fmt_stream in streaming_formats:
                    # Live adaptive https formats are not supported: skip unless extractor-arg given
                    if fmt_stream.get('targetDurationSec') and skip_bad_formats:
                        continue

                    # FORMAT_STREAM_TYPE_OTF(otf=1) requires downloading the init fragment
                    # (adding `&sq=0` to the URL) and parsing emsg box to determine the
                    # number of fragment that would subsequently requested with (`&sq=N`)
                    if fmt_stream.get('type') == 'FORMAT_STREAM_TYPE_OTF' and not bool(fmt_stream.get('drmFamilies')):
                        continue

                    stream_id = get_stream_id(fmt_stream)
                    if not all_formats:
                        if stream_id in stream_ids:
                            continue

                    pot_policy: GvsPoTokenPolicy = self._get_default_ytcfg(client_name)['GVS_PO_TOKEN_POLICY'][StreamingProtocol.HTTPS]

                    require_po_token = (
                        stream_id[0] not in ['18']
                        and gvs_pot_required(pot_policy, is_premium_subscriber, player_token_provided))

                    po_token = (
                        gvs_pots.get(client_name)
                        or fetch_po_token_func(required=require_po_token or pot_policy.recommended))
                    if po_token:
                        if client_name not in gvs_pots:
                            gvs_pots[client_name] = po_token

                    fmt_url = fmt_stream.get('url')
                    encrypted_sig, sc = None, None
                    if not fmt_url:
                        # We still need to register original/default language information
                        # See: https://github.com/yt-dlp/yt-dlp/issues/14883
                        get_language_code_and_preference(fmt_stream)
                        sc = urllib.parse.parse_qs(fmt_stream.get('signatureCipher'))
                        fmt_url = traverse_obj(sc, ('url', 0, {url_or_none}))
                        encrypted_sig = traverse_obj(sc, ('s', 0))
                        if not all((sc, fmt_url, skip_player_js or player_url, encrypted_sig)):
                            msg_tmpl = (
                                '{}Some {} client https formats have been skipped as they are missing a URL. '
                                '{}. See  https://github.com/yt-dlp/yt-dlp/issues/12482  for more details')
                            if client_name in ('web', 'web_safari'):
                                self.write_debug(msg_tmpl.format(
                                    f'{video_id}: ', client_name,
                                    'YouTube is forcing SABR streaming for this client'), only_once=True)
                            else:
                                msg = (
                                    f'YouTube may have enabled the SABR-only streaming experiment for '
                                    f'{"your account" if self.is_authenticated else "the current session"}')
                                self.report_warning(msg_tmpl.format('', client_name, msg), video_id, only_once=True)
                            continue

                    fmt = process_format_stream(
                        fmt_stream, proto, missing_pot=require_po_token and not po_token,
                        super_resolution=is_super_resolution(fmt_url))
                    if not fmt:
                        continue

                    # signature
                    if encrypted_sig:
                        if skip_player_js:
                            continue
                        solve_js_challenges()
                        spec = self._load_player_data_from_cache(
                            'sigfuncs', player_url, len(encrypted_sig), use_disk_cache=True)
                        if not spec:
                            continue
                        fmt_url += '&{}={}'.format(
                            traverse_obj(sc, ('sp', -1)) or 'signature',
                            solve_sig(encrypted_sig, spec))

                    # n challenge
                    query = parse_qs(fmt_url)
                    if query.get('n'):
                        if skip_player_js:
                            continue
                        n_challenge = query['n'][0]
                        solve_js_challenges()
                        n_result = self._load_player_data_from_cache('n', player_url, n_challenge)
                        if not n_result:
                            continue
                        fmt_url = update_url_query(fmt_url, {'n': n_result})

                    if po_token:
                        fmt_url = update_url_query(fmt_url, {'pot': po_token})

                    fmt['url'] = fmt_url

                    if stream_id[0]:
                        itags[stream_id[0]].add((proto, fmt.get('language')))
                        stream_ids.append(stream_id)

                    # For handling potential pre-playback required waiting period
                    if live_status not in ('is_live', 'post_live'):
                        fmt['available_at'] = available_at

                    https_fmts.append(fmt)

                for fmt in https_fmts:
                    if (all_formats or 'dashy' in format_types) and fmt['filesize']:
                        yield {
                            **fmt,
                            'format_id': f'{fmt["format_id"]}-dashy' if all_formats else fmt['format_id'],
                            'protocol': 'http_dash_segments',
                            'fragments': build_fragments(fmt),
                        }
                    if all_formats or 'dashy' not in format_types:
                        fmt['downloader_options'] = {'http_chunk_size': CHUNK_SIZE}
                        yield fmt

            yield from process_https_formats()

            needs_live_processing = self._needs_live_processing(live_status, duration)

            skip_manifests = set(self._configuration_arg('skip'))
            if (needs_live_processing == 'is_live'  # These will be filtered out by YoutubeDL anyway
                    or (needs_live_processing and skip_bad_formats)):
                skip_manifests.add('hls')

            if skip_bad_formats and live_status == 'is_live' and needs_live_processing != 'is_live':
                skip_manifests.add('dash')

            def process_manifest_format(f, proto, client_name, itag, missing_pot):
                key = (proto, f.get('language'))
                if not all_formats and key in itags[itag]:
                    return False

                # For handling potential pre-playback required waiting period
                if live_status not in ('is_live', 'post_live'):
                    f['available_at'] = available_at

                if f.get('source_preference') is None:
                    f['source_preference'] = -1

                # Deprioritize since its pre-merged m3u8 formats may have lower quality audio streams
                if client_name == 'web_safari' and proto == 'hls' and live_status != 'is_live':
                    f['source_preference'] -= 1

                if missing_pot:
                    f['format_note'] = join_nonempty(f.get('format_note'), 'MISSING POT', delim=' ')
                    f['source_preference'] -= 20

                itags[itag].add(key)

                if itag and all_formats:
                    f['format_id'] = f'{itag}-{proto}'
                elif any(p != proto for p, _ in itags[itag]):
                    f['format_id'] = f'{itag}-{proto}'
                elif itag:
                    f['format_id'] = itag

                lang_code = f.get('language')
                if lang_code and lang_code == language_map[ORIGINAL_LANG_VALUE]:
                    f['format_note'] = join_nonempty(f.get('format_note'), '(original)', delim=' ')
                    f['language_preference'] = ORIGINAL_LANG_VALUE
                elif lang_code and lang_code == language_map[DEFAULT_LANG_VALUE]:
                    f['format_note'] = join_nonempty(f.get('format_note'), '(default)', delim=' ')
                    f['language_preference'] = DEFAULT_LANG_VALUE

                if itag in ('616', '235'):
                    f['format_note'] = join_nonempty(f.get('format_note'), 'Premium', delim=' ')
                    f['source_preference'] += 100

                f['quality'] = q(itag_qualities.get(try_get(f, lambda f: f['format_id'].split('-')[0]), -1))
                if f['quality'] == -1 and f.get('height'):
                    f['quality'] = q(res_qualities[min(res_qualities, key=lambda x: abs(x - f['height']))])
                if self.get_param('verbose') or all_formats:
                    f['format_note'] = join_nonempty(
                        f.get('format_note'), short_client_name(client_name), delim=', ')
                if f.get('fps') and f['fps'] <= 1:
                    del f['fps']

                if proto == 'hls' and f.get('has_drm'):
                    f['has_drm'] = 'maybe'
                    f['source_preference'] -= 5
                return True

            hls_manifest_url = 'hls' not in skip_manifests and streaming_data.get('hlsManifestUrl')
            if hls_manifest_url:
                manifest_path = urllib.parse.urlparse(hls_manifest_url).path
                if m := re.fullmatch(r'(?P<path>.+)(?P<suffix>/(?:file|playlist)/index\.m3u8)', manifest_path):
                    manifest_path, manifest_suffix = m.group('path', 'suffix')
                else:
                    manifest_suffix = ''

                solved_n = False
                n_challenge = get_manifest_n_challenge(hls_manifest_url)
                if n_challenge and not skip_player_js:
                    solve_js_challenges()
                    n_result = self._load_player_data_from_cache('n', player_url, n_challenge)
                    if n_result:
                        manifest_path = manifest_path.replace(f'/n/{n_challenge}', f'/n/{n_result}')
                        solved_n = n_result in manifest_path

                pot_policy: GvsPoTokenPolicy = self._get_default_ytcfg(
                    client_name)['GVS_PO_TOKEN_POLICY'][StreamingProtocol.HLS]
                require_po_token = gvs_pot_required(pot_policy, is_premium_subscriber, player_token_provided)
                po_token = gvs_pots.get(client_name, fetch_po_token_func(required=require_po_token or pot_policy.recommended))
                if po_token:
                    manifest_path = manifest_path.rstrip('/') + f'/pot/{po_token}'
                    if client_name not in gvs_pots:
                        gvs_pots[client_name] = po_token

                if require_po_token and not po_token and 'missing_pot' not in self._configuration_arg('formats'):
                    self._report_pot_format_skipped(video_id, client_name, 'hls')
                elif solved_n or not n_challenge:
                    hls_manifest_url = update_url(hls_manifest_url, path=f'{manifest_path}{manifest_suffix}')
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        hls_manifest_url, video_id, 'mp4', fatal=False, live=live_status == 'is_live')
                    for sub in traverse_obj(subs, (..., ..., {dict})):
                        # TODO: If HLS video requires a PO Token, do the subs also require pot?
                        # Save client name for debugging
                        sub[STREAMING_DATA_CLIENT_NAME] = client_name
                    subtitles = self._merge_subtitles(subs, subtitles)
                    for f in fmts:
                        if process_manifest_format(f, 'hls', client_name, self._search_regex(
                                r'/itag/(\d+)', f['url'], 'itag', default=None), require_po_token and not po_token):
                            yield f

            dash_manifest_url = 'dash' not in skip_manifests and streaming_data.get('dashManifestUrl')
            if dash_manifest_url:
                manifest_path = urllib.parse.urlparse(dash_manifest_url).path

                solved_n = False
                n_challenge = get_manifest_n_challenge(dash_manifest_url)
                if n_challenge and not skip_player_js:
                    solve_js_challenges()
                    n_result = self._load_player_data_from_cache('n', player_url, n_challenge)
                    if n_result:
                        manifest_path = manifest_path.replace(f'/n/{n_challenge}', f'/n/{n_result}')
                        solved_n = n_result in manifest_path

                pot_policy: GvsPoTokenPolicy = self._get_default_ytcfg(
                    client_name)['GVS_PO_TOKEN_POLICY'][StreamingProtocol.DASH]
                require_po_token = gvs_pot_required(pot_policy, is_premium_subscriber, player_token_provided)
                po_token = gvs_pots.get(client_name, fetch_po_token_func(required=require_po_token or pot_policy.recommended))
                if po_token:
                    manifest_path = manifest_path.rstrip('/') + f'/pot/{po_token}'
                    if client_name not in gvs_pots:
                        gvs_pots[client_name] = po_token

                if require_po_token and not po_token and 'missing_pot' not in self._configuration_arg('formats'):
                    self._report_pot_format_skipped(video_id, client_name, 'dash')
                elif solved_n or not n_challenge:
                    dash_manifest_url = update_url(dash_manifest_url, path=manifest_path)
                    formats, subs = self._extract_mpd_formats_and_subtitles(dash_manifest_url, video_id, fatal=False)
                    for sub in traverse_obj(subs, (..., ..., {dict})):
                        # TODO: If DASH video requires a PO Token, do the subs also require pot?
                        # Save client name for debugging
                        sub[STREAMING_DATA_CLIENT_NAME] = client_name
                    subtitles = self._merge_subtitles(subs, subtitles)  # Prioritize HLS subs over DASH
                    for f in formats:
                        # Save original itag value as format_id because process_manifest_format mutates f
                        format_id = f['format_id']
                        if process_manifest_format(f, 'dash', client_name, format_id, require_po_token and not po_token):
                            f['filesize'] = int_or_none(self._search_regex(
                                r'/clen/(\d+)', f.get('fragment_base_url') or f['url'], 'file size', default=None))
                            if needs_live_processing:
                                f['is_from_start'] = True
                                f['_itag'] = format_id
                                f['_client'] = client_name
                            yield f
        yield subtitles