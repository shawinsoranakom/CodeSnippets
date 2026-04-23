def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)

        base_url = self.http_scheme() + '//www.youtube.com/'
        webpage_url = base_url + 'watch?v=' + video_id

        webpage, webpage_ytcfg, initial_data, is_premium_subscriber, player_responses, player_url = self._initial_extract(
            url, smuggled_data, webpage_url, self._webpage_client, video_id)

        playability_statuses = traverse_obj(
            player_responses, (..., 'playabilityStatus'), expected_type=dict)

        trailer_video_id = get_first(
            playability_statuses,
            ('errorScreen', 'playerLegacyDesktopYpcTrailerRenderer', 'trailerVideoId'),
            expected_type=str)
        if trailer_video_id:
            return self.url_result(
                trailer_video_id, self.ie_key(), trailer_video_id)

        search_meta = ((lambda x: self._html_search_meta(x, webpage, default=None))
                       if webpage else (lambda x: None))

        video_details = traverse_obj(player_responses, (..., 'videoDetails'), expected_type=dict)
        microformats = traverse_obj(
            player_responses, (..., 'microformat', 'playerMicroformatRenderer'),
            expected_type=dict)

        # Fallbacks in case player responses are missing metadata
        initial_sdcr = traverse_obj(initial_data, (
            'engagementPanels', ..., 'engagementPanelSectionListRenderer',
            'content', 'structuredDescriptionContentRenderer', {dict}, any))
        initial_description = traverse_obj(initial_sdcr, (
            'items', ..., 'expandableVideoDescriptionBodyRenderer',
            'attributedDescriptionBodyText', 'content', {str}, any))
        # videoDescriptionHeaderRenderer also has publishDate/channel/handle/ucid, but not needed
        initial_vdhr = traverse_obj(initial_sdcr, (
            'items', ..., 'videoDescriptionHeaderRenderer', {dict}, any)) or {}
        initial_video_details_renderer = traverse_obj(initial_data, (
            'playerOverlays', 'playerOverlayRenderer', 'videoDetails',
            'playerOverlayVideoDetailsRenderer', {dict})) or {}
        initial_title = (
            self._get_text(initial_vdhr, 'title')
            or self._get_text(initial_video_details_renderer, 'title'))

        translated_title = self._get_text(microformats, (..., 'title'))
        video_title = ((self._preferred_lang and translated_title)
                       or get_first(video_details, 'title')  # primary
                       or translated_title
                       or search_meta(['og:title', 'twitter:title', 'title']))
        if not video_title and initial_title:
            self.report_warning(
                'No title found in player responses; falling back to title from initial data. '
                'Other metadata may also be missing')
            video_title = initial_title
        translated_description = self._get_text(microformats, (..., 'description'))
        original_description = get_first(video_details, 'shortDescription')
        video_description = (
            (self._preferred_lang and translated_description)
            # If original description is blank, it will be an empty string.
            # Do not prefer translated description in this case.
            or original_description if original_description is not None else translated_description)
        if video_description is None:
            video_description = initial_description

        multifeed_metadata_list = get_first(
            player_responses,
            ('multicamera', 'playerLegacyMulticameraRenderer', 'metadataList'),
            expected_type=str)
        if multifeed_metadata_list and not smuggled_data.get('force_singlefeed'):
            if self.get_param('noplaylist'):
                self.to_screen(f'Downloading just video {video_id} because of --no-playlist')
            else:
                entries = []
                feed_ids = []
                for feed in multifeed_metadata_list.split(','):
                    # Unquote should take place before split on comma (,) since textual
                    # fields may contain comma as well (see
                    # https://github.com/ytdl-org/youtube-dl/issues/8536)
                    feed_data = urllib.parse.parse_qs(
                        urllib.parse.unquote_plus(feed))

                    def feed_entry(name):
                        return try_get(
                            feed_data, lambda x: x[name][0], str)

                    feed_id = feed_entry('id')
                    if not feed_id:
                        continue
                    feed_title = feed_entry('title')
                    title = video_title
                    if feed_title:
                        title += f' ({feed_title})'
                    entries.append({
                        '_type': 'url_transparent',
                        'ie_key': 'Youtube',
                        'url': smuggle_url(
                            '{}watch?v={}'.format(base_url, feed_data['id'][0]),
                            {'force_singlefeed': True}),
                        'title': title,
                    })
                    feed_ids.append(feed_id)
                self.to_screen(
                    'Downloading multifeed video ({}) - add --no-playlist to just download video {}'.format(
                        ', '.join(feed_ids), video_id))
                return self.playlist_result(
                    entries, video_id, video_title, video_description)

        duration = (int_or_none(get_first(video_details, 'lengthSeconds'))
                    or int_or_none(get_first(microformats, 'lengthSeconds'))
                    or parse_duration(search_meta('duration')) or None)

        live_broadcast_details, live_status, formats, automatic_captions = \
            self._list_formats(video_id, microformats, video_details, player_responses, player_url, duration)
        streaming_data = traverse_obj(player_responses, (..., 'streamingData'))
        if live_status == 'post_live':
            self.write_debug(f'{video_id}: Video is in Post-Live Manifestless mode')

        if not formats:
            if not self.get_param('allow_unplayable_formats') and traverse_obj(streaming_data, (..., 'licenseInfos')):
                self.report_drm(video_id)
            pemr = get_first(
                playability_statuses,
                ('errorScreen', 'playerErrorMessageRenderer'), expected_type=dict) or {}
            reason = self._get_text(pemr, 'reason') or get_first(playability_statuses, 'reason')
            subreason = clean_html(self._get_text(pemr, 'subreason') or '')
            if subreason:
                if subreason.startswith('The uploader has not made this video available in your country'):
                    countries = get_first(microformats, 'availableCountries')
                    if not countries:
                        regions_allowed = search_meta('regionsAllowed')
                        countries = regions_allowed.split(',') if regions_allowed else None
                    self.raise_geo_restricted(subreason, countries, metadata_available=True)
                reason += f'. {subreason}'
            if reason:
                if 'sign in' in reason.lower():
                    reason = remove_end(reason, 'This helps protect our community. Learn more')
                    reason = f'{remove_end(reason.strip(), ".")}. {self._youtube_login_hint}'
                elif get_first(playability_statuses, ('errorScreen', 'playerCaptchaViewModel', {dict})):
                    reason += '. YouTube is requiring a captcha challenge before playback'
                elif "This content isn't available, try again later" in reason:
                    reason = (
                        f'{remove_end(reason.strip(), ".")}. {"Your account" if self.is_authenticated else "The current session"} '
                        f'has been rate-limited by YouTube for up to an hour. It is recommended to use `-t sleep` to add a delay '
                        f'between video requests to avoid exceeding the rate limit. For more information, refer to  '
                        f'https://github.com/yt-dlp/yt-dlp/wiki/Extractors#this-content-isnt-available-try-again-later'
                    )
                self.raise_no_formats(reason, expected=True)

        keywords = get_first(video_details, 'keywords', expected_type=list) or []
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
        thumbnails = self._extract_thumbnails((video_details, microformats), (..., ..., 'thumbnail'))
        thumbnail_url = search_meta(['og:image', 'twitter:image'])
        if thumbnail_url:
            thumbnails.append({
                'url': thumbnail_url,
            })
        original_thumbnails = thumbnails.copy()

        # The best resolution thumbnails sometimes does not appear in the webpage
        # See: https://github.com/yt-dlp/yt-dlp/issues/340
        # List of possible thumbnails - Ref: <https://stackoverflow.com/a/20542029>
        thumbnail_names = [
            # While the *1,*2,*3 thumbnails are just below their corresponding "*default" variants
            # in resolution, these are not the custom thumbnail. So de-prioritize them
            'maxresdefault', 'hq720', 'sddefault', 'hqdefault', '0', 'mqdefault', 'default',
            'sd1', 'sd2', 'sd3', 'hq1', 'hq2', 'hq3', 'mq1', 'mq2', 'mq3', '1', '2', '3',
        ]
        n_thumbnail_names = len(thumbnail_names)
        thumbnails.extend({
            'url': 'https://i.ytimg.com/vi{webp}/{video_id}/{name}{live}.{ext}'.format(
                video_id=video_id, name=name, ext=ext,
                webp='_webp' if ext == 'webp' else '', live='_live' if live_status == 'is_live' else ''),
        } for name in thumbnail_names for ext in ('webp', 'jpg'))
        for thumb in thumbnails:
            i = next((i for i, t in enumerate(thumbnail_names) if f'/{video_id}/{t}' in thumb['url']), n_thumbnail_names)
            thumb['preference'] = (0 if '.webp' in thumb['url'] else -1) - (2 * i)
        self._remove_duplicate_formats(thumbnails)
        self._downloader._sort_thumbnails(original_thumbnails)

        category = get_first(microformats, 'category') or search_meta('genre')
        channel_id = self.ucid_or_none(str_or_none(
            get_first(video_details, 'channelId')
            or get_first(microformats, 'externalChannelId')
            or search_meta('channelId')))
        owner_profile_url = get_first(microformats, 'ownerProfileUrl')

        live_start_time = parse_iso8601(get_first(live_broadcast_details, 'startTimestamp'))
        live_end_time = parse_iso8601(get_first(live_broadcast_details, 'endTimestamp'))
        if not duration and live_end_time and live_start_time:
            duration = live_end_time - live_start_time

        needs_live_processing = self._needs_live_processing(live_status, duration)

        def adjust_incomplete_format(fmt, note_suffix='(Last 2 hours)', pref_adjustment=-10):
            fmt['preference'] = (fmt.get('preference') or -1) + pref_adjustment
            fmt['format_note'] = join_nonempty(fmt.get('format_note'), note_suffix, delim=' ')

        # Adjust preference and format note for incomplete live/post-live formats
        if live_status in ('is_live', 'post_live'):
            for fmt in formats:
                protocol = fmt.get('protocol')
                # Currently, protocol isn't set for adaptive https formats, but this could change
                is_adaptive = protocol in (None, 'http', 'https')
                if live_status == 'post_live' and is_adaptive:
                    # Post-live adaptive formats cause HttpFD to raise "Did not get any data blocks"
                    # These formats are *only* useful to external applications, so we can hide them
                    # Set their preference <= -1000 so that FormatSorter flags them as 'hidden'
                    adjust_incomplete_format(fmt, note_suffix='(ended)', pref_adjustment=-5000)
                # Is it live with --live-from-start? Or is it post-live and its duration is >2hrs?
                elif needs_live_processing:
                    if not fmt.get('is_from_start'):
                        # Post-live m3u8 formats for >2hr streams
                        adjust_incomplete_format(fmt)
                elif live_status == 'is_live':
                    if protocol == 'http_dash_segments':
                        # Live DASH formats without --live-from-start
                        adjust_incomplete_format(fmt)
                    elif is_adaptive:
                        # Incomplete live adaptive https formats
                        adjust_incomplete_format(fmt, note_suffix='(incomplete)', pref_adjustment=-20)

        if needs_live_processing:
            self._prepare_live_from_start_formats(
                formats, video_id, live_start_time, url, webpage_url, smuggled_data, live_status == 'is_live')

        formats.extend(self._extract_storyboard(player_responses, duration))

        channel_handle = self.handle_from_url(owner_profile_url)

        info = {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'thumbnails': thumbnails,
            # The best thumbnail that we are sure exists. Prevents unnecessary
            # URL checking if user don't care about getting the best possible thumbnail
            'thumbnail': traverse_obj(original_thumbnails, (-1, 'url')),
            'description': video_description,
            'channel_id': channel_id,
            'channel_url': format_field(channel_id, None, 'https://www.youtube.com/channel/%s', default=None),
            'duration': duration,
            'view_count': int_or_none(
                get_first((video_details, microformats), (..., 'viewCount'))
                or search_meta('interactionCount')),
            'average_rating': float_or_none(get_first(video_details, 'averageRating')),
            'age_limit': 18 if (
                get_first(microformats, 'isFamilySafe') is False
                or search_meta('isFamilyFriendly') == 'false'
                or search_meta('og:restrictions:age') == '18+') else 0,
            'webpage_url': webpage_url,
            'categories': [category] if category else None,
            'tags': keywords,
            'playable_in_embed': get_first(playability_statuses, 'playableInEmbed'),
            'live_status': live_status,
            'media_type': (
                'livestream' if get_first(video_details, 'isLiveContent')
                else 'short' if get_first(microformats, 'isShortsEligible')
                else 'video'),
            'release_timestamp': live_start_time,
            '_format_sort_fields': (  # source_preference is lower for potentially damaged formats
                'quality', 'res', 'fps', 'hdr:12', 'source',
                'vcodec:vp9.2' if 'prefer-vp9-sort' in self.get_param('compat_opts', []) else 'vcodec',
                'channels', 'acodec', 'lang', 'proto'),
        }

        def get_lang_code(track):
            return (remove_start(track.get('vssId') or '', '.').replace('.', '-')
                    or track.get('languageCode'))

        def process_language(container, base_url, lang_code, sub_name, client_name, query):
            lang_subs = container.setdefault(lang_code, [])
            for fmt in self._SUBTITLE_FORMATS:
                # xosf=1 results in undesirable text position data for vtt, json3 & srv* subtitles
                # See: https://github.com/yt-dlp/yt-dlp/issues/13654
                query = {**query, 'fmt': fmt, 'xosf': []}
                lang_subs.append({
                    'ext': fmt,
                    'url': urljoin('https://www.youtube.com', update_url_query(base_url, query)),
                    'name': sub_name,
                    'impersonate': True,
                    STREAMING_DATA_CLIENT_NAME: client_name,
                })

        def set_audio_lang_from_orig_subs_lang(lang_code):
            for f in formats:
                if f.get('acodec') != 'none' and not f.get('language'):
                    f['language'] = lang_code

        subtitles = {}
        skipped_subs_clients = set()

        # Only web/mweb clients provide translationLanguages, so include initial_pr in the traversal
        translation_languages = {
            lang['languageCode']: self._get_text(lang['languageName'], max_runs=1)
            for lang in traverse_obj(player_responses, (
                ..., 'captions', 'playerCaptionsTracklistRenderer', 'translationLanguages',
                lambda _, v: v['languageCode'] and v['languageName']))
        }
        # NB: Constructing the full subtitle dictionary is slow
        get_translated_subs = 'translated_subs' not in self._configuration_arg('skip') and (
            self.get_param('writeautomaticsub', False) or self.get_param('listsubtitles'))

        # Filter out initial_pr which does not have streamingData (smuggled client context)
        prs = traverse_obj(player_responses, (
            lambda _, v: v['streamingData'] and v['captions']['playerCaptionsTracklistRenderer']))
        all_captions = traverse_obj(prs, (
            ..., 'captions', 'playerCaptionsTracklistRenderer', 'captionTracks', ..., {dict}))
        need_subs_langs = {get_lang_code(sub) for sub in all_captions if sub.get('kind') != 'asr'}
        need_caps_langs = {
            remove_start(get_lang_code(sub), 'a-')
            for sub in all_captions if sub.get('kind') == 'asr'}

        for pr in prs:
            pctr = pr['captions']['playerCaptionsTracklistRenderer']
            client_name = pr['streamingData'][STREAMING_DATA_CLIENT_NAME]
            innertube_client_name = pr['streamingData'][STREAMING_DATA_INNERTUBE_CONTEXT]['client']['clientName']
            pot_policy: GvsPoTokenPolicy = self._get_default_ytcfg(client_name)['SUBS_PO_TOKEN_POLICY']
            fetch_subs_po_token_func = pr['streamingData'][STREAMING_DATA_FETCH_SUBS_PO_TOKEN]

            pot_params = {}
            already_fetched_pot = False

            for caption_track in traverse_obj(pctr, ('captionTracks', lambda _, v: v['baseUrl'])):
                base_url = caption_track['baseUrl']
                qs = parse_qs(base_url)
                lang_code = get_lang_code(caption_track)
                requires_pot = (
                    # We can detect the experiment for now
                    any(e in traverse_obj(qs, ('exp', ...)) for e in ('xpe', 'xpv'))
                    or (pot_policy.required and not (pot_policy.not_required_for_premium and is_premium_subscriber)))

                if not already_fetched_pot:
                    already_fetched_pot = True
                    if subs_po_token := fetch_subs_po_token_func(required=requires_pot or pot_policy.recommended):
                        pot_params.update({
                            'pot': subs_po_token,
                            'potc': '1',
                            'c': innertube_client_name,
                        })

                if not pot_params and requires_pot:
                    skipped_subs_clients.add(client_name)
                    self._report_pot_subtitles_skipped(video_id, client_name)
                    break

                orig_lang = qs.get('lang', [None])[-1]
                lang_name = self._get_text(caption_track, 'name', max_runs=1)
                is_manual_subs = caption_track.get('kind') != 'asr'
                if is_manual_subs:
                    if not lang_code:
                        continue
                    process_language(
                        subtitles, base_url, lang_code, lang_name, client_name, pot_params)
                    if not caption_track.get('isTranslatable'):
                        continue
                for trans_code, trans_name in translation_languages.items():
                    if not trans_code:
                        continue
                    orig_trans_code = trans_code
                    if is_manual_subs and trans_code != 'und':
                        if not get_translated_subs:
                            continue
                        trans_code += f'-{lang_code}'
                        trans_name += format_field(lang_name, None, ' from %s')
                    if lang_code == f'a-{orig_trans_code}':
                        # Set audio language based on original subtitles
                        set_audio_lang_from_orig_subs_lang(orig_trans_code)
                        # Add an "-orig" label to the original language so that it can be distinguished.
                        # The subs are returned without "-orig" as well for compatibility
                        process_language(
                            automatic_captions, base_url, f'{trans_code}-orig',
                            f'{trans_name} (Original)', client_name, pot_params)
                    # Setting tlang=lang returns damaged subtitles.
                    process_language(
                        automatic_captions, base_url, trans_code, trans_name, client_name,
                        pot_params if orig_lang == orig_trans_code else {'tlang': trans_code, **pot_params})

                # Extract automatic captions when the language is not in 'translationLanguages'
                # e.g. Cantonese [yue], see https://github.com/yt-dlp/yt-dlp/issues/14889
                lang_code = remove_start(lang_code, 'a-')
                if is_manual_subs or not lang_code or lang_code in automatic_captions:
                    continue
                lang_name = remove_end(lang_name, ' (auto-generated)')
                if caption_track.get('isTranslatable'):
                    # We can assume this is the original audio language
                    set_audio_lang_from_orig_subs_lang(lang_code)
                    process_language(
                        automatic_captions, base_url, f'{lang_code}-orig',
                        f'{lang_name} (Original)', client_name, pot_params)
                process_language(
                    automatic_captions, base_url, lang_code, lang_name, client_name, pot_params)

            # Avoid duplication if we've already got everything we need
            need_subs_langs.difference_update(subtitles)
            need_caps_langs.difference_update(automatic_captions)
            if not (need_subs_langs or need_caps_langs):
                break

        if skipped_subs_clients and (need_subs_langs or need_caps_langs):
            self._report_pot_subtitles_skipped(video_id, True, msg=join_nonempty(
                f'{video_id}: There are missing subtitles languages because a PO token was not provided.',
                need_subs_langs and f'Subtitles for these languages are missing: {", ".join(need_subs_langs)}.',
                need_caps_langs and f'Automatic captions for {len(need_caps_langs)} languages are missing.',
                delim=' '))

        info['automatic_captions'] = automatic_captions
        info['subtitles'] = subtitles

        parsed_url = urllib.parse.urlparse(url)
        for component in [parsed_url.fragment, parsed_url.query]:
            query = urllib.parse.parse_qs(component)
            for k, v in query.items():
                for d_k, s_ks in [('start', ('start', 't')), ('end', ('end',))]:
                    d_k += '_time'
                    if d_k not in info and k in s_ks:
                        info[d_k] = parse_duration(v[0])

        # Youtube Music Auto-generated description
        if (video_description or '').strip().endswith('\nAuto-generated by YouTube.'):
            mobj = re.search(
                r'''(?xs)
                    (?:\n|^)(?P<track>[^\n·]+)\ ·\ (?P<artist>[^\n]+)\n+
                    (?P<album>[^\n]+)\n+
                    (?:℗\s*(?P<release_year>\d{4}))?
                    (?:.+?\nReleased\ on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?
                    (?:.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+)\n)?
                    .+\nAuto-generated\ by\ YouTube\.\s*$
                ''', video_description)
            if mobj:
                release_year = mobj.group('release_year')
                release_date = mobj.group('release_date')
                if release_date:
                    release_date = release_date.replace('-', '')
                    if not release_year:
                        release_year = release_date[:4]
                info.update({
                    'album': mobj.group('album'.strip()),
                    'artists': ([a] if (a := mobj.group('clean_artist'))
                                else [a.strip() for a in mobj.group('artist').split(' · ')]),
                    'track': mobj.group('track').strip(),
                    'release_date': release_date,
                    'release_year': int_or_none(release_year),
                })

        COMMENTS_SECTION_IDS = ('comment-item-section', 'engagement-panel-comments-section')
        info['comment_count'] = traverse_obj(initial_data, (
            'contents', 'twoColumnWatchNextResults', 'results', 'results', 'contents', ..., 'itemSectionRenderer',
            'contents', ..., 'commentsEntryPointHeaderRenderer', 'commentCount',
        ), (
            'engagementPanels', lambda _, v: v['engagementPanelSectionListRenderer']['panelIdentifier'] in COMMENTS_SECTION_IDS,
            'engagementPanelSectionListRenderer', 'header', 'engagementPanelTitleHeaderRenderer', 'contextualInfo',
        ), expected_type=self._get_count, get_all=False)

        try:  # This will error if there is no livechat
            initial_data['contents']['twoColumnWatchNextResults']['conversationBar']['liveChatRenderer']['continuations'][0]['reloadContinuationData']['continuation']
        except (KeyError, IndexError, TypeError):
            pass
        else:
            info.setdefault('subtitles', {})['live_chat'] = [{
                # url is needed to set cookies
                'url': f'https://www.youtube.com/watch?v={video_id}&bpctr=9999999999&has_verified=1',
                'video_id': video_id,
                'ext': 'json',
                'protocol': ('youtube_live_chat' if live_status in ('is_live', 'is_upcoming')
                             else 'youtube_live_chat_replay'),
            }]

        if initial_data:
            info['chapters'] = (
                self._extract_chapters_from_json(initial_data, duration)
                or self._extract_chapters_from_engagement_panel(initial_data, duration)
                or self._extract_chapters_from_description(video_description, duration)
                or None)

            info['heatmap'] = self._extract_heatmap(initial_data)

        contents = traverse_obj(
            initial_data, ('contents', 'twoColumnWatchNextResults', 'results', 'results', 'contents'),
            expected_type=list, default=[])

        vpir = get_first(contents, 'videoPrimaryInfoRenderer')
        if vpir:
            stl = vpir.get('superTitleLink')
            if stl:
                stl = self._get_text(stl)
                if try_get(
                        vpir,
                        lambda x: x['superTitleIcon']['iconType']) == 'LOCATION_PIN':
                    info['location'] = stl
                else:
                    mobj = re.search(r'(.+?)\s*S(\d+)\s*•?\s*E(\d+)', stl)
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
                tbrs = variadic(
                    traverse_obj(
                        tlb, ('toggleButtonRenderer', ...),
                        ('segmentedLikeDislikeButtonRenderer', ..., 'toggleButtonRenderer')))
                for tbr in tbrs:
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

            info['like_count'] = traverse_obj(vpir, (
                'videoActions', 'menuRenderer', 'topLevelButtons', ...,
                'segmentedLikeDislikeButtonViewModel', 'likeButtonViewModel', 'likeButtonViewModel',
                'toggleButtonViewModel', 'toggleButtonViewModel', 'defaultButtonViewModel',
                'buttonViewModel', 'accessibilityText', {parse_count}), get_all=False)

            vcr = traverse_obj(vpir, ('viewCount', 'videoViewCountRenderer'))
            if vcr:
                vc = self._get_count(vcr, 'viewCount')
                # Upcoming premieres with waiting count are treated as live here
                if vcr.get('isLive'):
                    info['concurrent_view_count'] = vc
                elif info.get('view_count') is None:
                    info['view_count'] = vc

        vsir = get_first(contents, 'videoSecondaryInfoRenderer')
        if vsir:
            vor = traverse_obj(vsir, ('owner', 'videoOwnerRenderer'))
            collaborators = traverse_obj(vor, (
                'attributedTitle', 'commandRuns', ..., 'onTap', 'innertubeCommand', 'showDialogCommand',
                'panelLoadingStrategy', 'inlineContent', 'dialogViewModel', 'customContent', 'listViewModel',
                'listItems', ..., 'listItemViewModel', 'title', 'content', {str}))
            info.update({
                'channel': self._get_text(vor, 'title') or (collaborators[0] if collaborators else None),
                'channel_follower_count': self._get_count(vor, 'subscriberCountText'),
                'creators': collaborators if collaborators else None,
            })

            if not channel_handle:
                channel_handle = self.handle_from_url(
                    traverse_obj(vor, (
                        ('navigationEndpoint', ('title', 'runs', ..., 'navigationEndpoint')),
                        (('commandMetadata', 'webCommandMetadata', 'url'), ('browseEndpoint', 'canonicalBaseUrl')),
                        {str}), get_all=False))

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
                mrr_title = self._get_text(mrr, 'title')
                mrr_contents_text = self._get_text(mrr, ('contents', 0))
                if mrr_title == 'License':
                    info['license'] = mrr_contents_text
                elif not multiple_songs:
                    if mrr_title == 'Album':
                        info['album'] = mrr_contents_text
                    elif mrr_title == 'Artist':
                        info['artists'] = [mrr_contents_text] if mrr_contents_text else None
                    elif mrr_title == 'Song':
                        info['track'] = mrr_contents_text
            owner_badges = self._extract_badges(traverse_obj(vsir, ('owner', 'videoOwnerRenderer', 'badges')))
            if self._has_badge(owner_badges, BadgeType.VERIFIED):
                info['channel_is_verified'] = True

        info.update({
            'uploader': info.get('channel'),
            'uploader_id': channel_handle,
            'uploader_url': format_field(channel_handle, None, 'https://www.youtube.com/%s', default=None),
        })

        # We only want timestamp IF it has time precision AND a timezone
        # Currently the uploadDate in microformats appears to be in US/Pacific timezone.
        timestamp = (
            parse_iso8601(get_first(microformats, 'uploadDate'), timezone=NO_DEFAULT)
            or parse_iso8601(search_meta('uploadDate'), timezone=NO_DEFAULT)
        )
        upload_date = (
            dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).strftime('%Y%m%d') if timestamp else
            (
                unified_strdate(get_first(microformats, 'uploadDate'))
                or unified_strdate(search_meta('uploadDate'))
            ))

        # In the case we cannot get the timestamp:
        # The upload date for scheduled, live and past live streams / premieres in microformats
        # may be different from the stream date. Although not in UTC, we will prefer it in this case.
        # See: https://github.com/yt-dlp/yt-dlp/pull/2223#issuecomment-1008485139
        if not upload_date or (not timestamp and live_status in ('not_live', None)):
            # this should be in UTC, as configured in the cookie/client context
            upload_date = strftime_or_none(
                self._parse_time_text(self._get_text(vpir, 'dateText'))) or upload_date

        info['upload_date'] = upload_date
        info['timestamp'] = timestamp

        if upload_date and live_status not in ('is_live', 'post_live', 'is_upcoming'):
            # Newly uploaded videos' HLS formats are potentially problematic and need to be checked
            upload_datetime = datetime_from_str(upload_date).replace(tzinfo=dt.timezone.utc)
            if upload_datetime >= datetime_from_str('today-2days'):
                for fmt in info['formats']:
                    if fmt.get('protocol') == 'm3u8_native':
                        fmt['__needs_testing'] = True

        for s_k, d_k in [('artists', 'creators'), ('track', 'alt_title')]:
            v = info.get(s_k)
            if v:
                info[d_k] = v

        badges = self._extract_badges(traverse_obj(vpir, 'badges'))

        is_private = (self._has_badge(badges, BadgeType.AVAILABILITY_PRIVATE)
                      or get_first(video_details, 'isPrivate', expected_type=bool))

        info['availability'] = (
            'public' if self._has_badge(badges, BadgeType.AVAILABILITY_PUBLIC)
            else self._availability(
                is_private=is_private,
                needs_premium=(
                    self._has_badge(badges, BadgeType.AVAILABILITY_PREMIUM)
                    or False if initial_data and is_private is not None else None),
                needs_subscription=(
                    self._has_badge(badges, BadgeType.AVAILABILITY_SUBSCRIPTION)
                    or False if initial_data and is_private is not None else None),
                needs_auth=info['age_limit'] >= 18,
                is_unlisted=None if is_private is None else (
                    self._has_badge(badges, BadgeType.AVAILABILITY_UNLISTED)
                    or get_first(microformats, 'isUnlisted', expected_type=bool))))

        info['__post_extractor'] = self.extract_comments(webpage_ytcfg, video_id, contents, webpage)

        self.mark_watched(video_id, player_responses)

        return info