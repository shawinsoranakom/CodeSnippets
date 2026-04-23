def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        json_ld_info = self._search_json_ld(webpage, playlist_id, default={})
        timestamp = json_ld_info.get('timestamp')

        playlist_title = json_ld_info.get('title')
        if not playlist_title:
            playlist_title = self._og_search_title(
                webpage, default=None) or self._html_search_regex(
                r'<title>(.+?)</title>', webpage, 'playlist title', default=None)
            if playlist_title:
                playlist_title = re.sub(r'(.+)\s*-\s*BBC.*?$', r'\1', playlist_title).strip()

        playlist_description = json_ld_info.get(
            'description') or self._og_search_description(webpage, default=None)

        if not timestamp:
            timestamp = parse_iso8601(self._search_regex(
                [r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"',
                 r'itemprop="datePublished"[^>]+datetime="([^"]+)"',
                 r'"datePublished":\s*"([^"]+)'],
                webpage, 'date', default=None))

        entries = []

        # article with multiple videos embedded with playlist.sxml (e.g.
        # http://www.bbc.com/sport/0/football/34475836)
        playlists = re.findall(r'<param[^>]+name="playlist"[^>]+value="([^"]+)"', webpage)
        playlists.extend(re.findall(r'data-media-id="([^"]+/playlist\.sxml)"', webpage))
        if playlists:
            entries = [
                self._extract_from_playlist_sxml(playlist_url, playlist_id, timestamp)
                for playlist_url in playlists]

        # news article with multiple videos embedded with data-playable
        data_playables = re.findall(r'data-playable=(["\'])({.+?})\1', webpage)
        if data_playables:
            for _, data_playable_json in data_playables:
                data_playable = self._parse_json(
                    unescapeHTML(data_playable_json), playlist_id, fatal=False)
                if not data_playable:
                    continue
                settings = data_playable.get('settings', {})
                if settings:
                    # data-playable with video vpid in settings.playlistObject.items (e.g.
                    # http://www.bbc.com/news/world-us-canada-34473351)
                    playlist_object = settings.get('playlistObject', {})
                    if playlist_object:
                        items = playlist_object.get('items')
                        if items and isinstance(items, list):
                            title = playlist_object['title']
                            description = playlist_object.get('summary')
                            duration = int_or_none(items[0].get('duration'))
                            programme_id = items[0].get('vpid')
                            formats, subtitles = self._download_media_selector(programme_id)
                            self._sort_formats(formats)
                            entries.append({
                                'id': programme_id,
                                'title': title,
                                'description': description,
                                'timestamp': timestamp,
                                'duration': duration,
                                'formats': formats,
                                'subtitles': subtitles,
                            })
                    else:
                        # data-playable without vpid but with a playlist.sxml URLs
                        # in otherSettings.playlist (e.g.
                        # http://www.bbc.com/turkce/multimedya/2015/10/151010_vid_ankara_patlama_ani)
                        playlist = data_playable.get('otherSettings', {}).get('playlist', {})
                        if playlist:
                            entry = None
                            for key in ('streaming', 'progressiveDownload'):
                                playlist_url = playlist.get('%sUrl' % key)
                                if not playlist_url:
                                    continue
                                try:
                                    info = self._extract_from_playlist_sxml(
                                        playlist_url, playlist_id, timestamp)
                                    if not entry:
                                        entry = info
                                    else:
                                        entry['title'] = info['title']
                                        entry['formats'].extend(info['formats'])
                                except ExtractorError as e:
                                    # Some playlist URL may fail with 500, at the same time
                                    # the other one may work fine (e.g.
                                    # http://www.bbc.com/turkce/haberler/2015/06/150615_telabyad_kentin_cogu)
                                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 500:
                                        continue
                                    raise
                            if entry:
                                self._sort_formats(entry['formats'])
                                entries.append(entry)

        if entries:
            return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)

        # http://www.bbc.co.uk/learningenglish/chinese/features/lingohack/ep-181227
        group_id = self._search_regex(
            r'<div[^>]+\bclass=["\']video["\'][^>]+\bdata-pid=["\'](%s)' % self._ID_REGEX,
            webpage, 'group id', default=None)
        if group_id:
            return self.url_result(
                'https://www.bbc.co.uk/programmes/%s' % group_id,
                ie=BBCCoUkIE.ie_key())

        # single video story (e.g. http://www.bbc.com/travel/story/20150625-sri-lankas-spicy-secret)
        programme_id = self._search_regex(
            [r'data-(?:video-player|media)-vpid="(%s)"' % self._ID_REGEX,
             r'<param[^>]+name="externalIdentifier"[^>]+value="(%s)"' % self._ID_REGEX,
             r'videoId\s*:\s*["\'](%s)["\']' % self._ID_REGEX],
            webpage, 'vpid', default=None)

        if programme_id:
            formats, subtitles = self._download_media_selector(programme_id)
            self._sort_formats(formats)
            # digitalData may be missing (e.g. http://www.bbc.com/autos/story/20130513-hyundais-rock-star)
            digital_data = self._parse_json(
                self._search_regex(
                    r'var\s+digitalData\s*=\s*({.+?});?\n', webpage, 'digital data', default='{}'),
                programme_id, fatal=False)
            page_info = digital_data.get('page', {}).get('pageInfo', {})
            title = page_info.get('pageName') or self._og_search_title(webpage)
            description = page_info.get('description') or self._og_search_description(webpage)
            timestamp = parse_iso8601(page_info.get('publicationDate')) or timestamp
            return {
                'id': programme_id,
                'title': title,
                'description': description,
                'timestamp': timestamp,
                'formats': formats,
                'subtitles': subtitles,
            }

        # bbc reel (e.g. https://www.bbc.com/reel/video/p07c6sb6/how-positive-thinking-is-harming-your-happiness)
        initial_data = self._parse_json(self._html_search_regex(
            r'<script[^>]+id=(["\'])initial-data\1[^>]+data-json=(["\'])(?P<json>(?:(?!\2).)+)',
            webpage, 'initial data', default='{}', group='json'), playlist_id, fatal=False)
        if initial_data:
            init_data = try_get(
                initial_data, lambda x: x['initData']['items'][0], dict) or {}
            smp_data = init_data.get('smpData') or {}
            clip_data = try_get(smp_data, lambda x: x['items'][0], dict) or {}
            version_id = clip_data.get('versionID')
            if version_id:
                title = smp_data['title']
                formats, subtitles = self._download_media_selector(version_id)
                self._sort_formats(formats)
                image_url = smp_data.get('holdingImageURL')
                display_date = init_data.get('displayDate')
                topic_title = init_data.get('topicTitle')

                return {
                    'id': version_id,
                    'title': title,
                    'formats': formats,
                    'alt_title': init_data.get('shortTitle'),
                    'thumbnail': image_url.replace('$recipe', 'raw') if image_url else None,
                    'description': smp_data.get('summary') or init_data.get('shortSummary'),
                    'upload_date': display_date.replace('-', '') if display_date else None,
                    'subtitles': subtitles,
                    'duration': int_or_none(clip_data.get('duration')),
                    'categories': [topic_title] if topic_title else None,
                }

        # Morph based embed (e.g. http://www.bbc.co.uk/sport/live/olympics/36895975)
        # There are several setPayload calls may be present but the video
        # seems to be always related to the first one
        morph_payload = self._parse_json(
            self._search_regex(
                r'Morph\.setPayload\([^,]+,\s*({.+?})\);',
                webpage, 'morph payload', default='{}'),
            playlist_id, fatal=False)
        if morph_payload:
            components = try_get(morph_payload, lambda x: x['body']['components'], list) or []
            for component in components:
                if not isinstance(component, dict):
                    continue
                lead_media = try_get(component, lambda x: x['props']['leadMedia'], dict)
                if not lead_media:
                    continue
                identifiers = lead_media.get('identifiers')
                if not identifiers or not isinstance(identifiers, dict):
                    continue
                programme_id = identifiers.get('vpid') or identifiers.get('playablePid')
                if not programme_id:
                    continue
                title = lead_media.get('title') or self._og_search_title(webpage)
                formats, subtitles = self._download_media_selector(programme_id)
                self._sort_formats(formats)
                description = lead_media.get('summary')
                uploader = lead_media.get('masterBrand')
                uploader_id = lead_media.get('mid')
                duration = None
                duration_d = lead_media.get('duration')
                if isinstance(duration_d, dict):
                    duration = parse_duration(dict_get(
                        duration_d, ('rawDuration', 'formattedDuration', 'spokenDuration')))
                return {
                    'id': programme_id,
                    'title': title,
                    'description': description,
                    'duration': duration,
                    'uploader': uploader,
                    'uploader_id': uploader_id,
                    'formats': formats,
                    'subtitles': subtitles,
                }

        preload_state = self._parse_json(self._search_regex(
            r'window\.__PRELOADED_STATE__\s*=\s*({.+?});', webpage,
            'preload state', default='{}'), playlist_id, fatal=False)
        if preload_state:
            current_programme = preload_state.get('programmes', {}).get('current') or {}
            programme_id = current_programme.get('id')
            if current_programme and programme_id and current_programme.get('type') == 'playable_item':
                title = current_programme.get('titles', {}).get('tertiary') or playlist_title
                formats, subtitles = self._download_media_selector(programme_id)
                self._sort_formats(formats)
                synopses = current_programme.get('synopses') or {}
                network = current_programme.get('network') or {}
                duration = int_or_none(
                    current_programme.get('duration', {}).get('value'))
                thumbnail = None
                image_url = current_programme.get('image_url')
                if image_url:
                    thumbnail = image_url.replace('{recipe}', 'raw')
                return {
                    'id': programme_id,
                    'title': title,
                    'description': dict_get(synopses, ('long', 'medium', 'short')),
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'uploader': network.get('short_title'),
                    'uploader_id': network.get('id'),
                    'formats': formats,
                    'subtitles': subtitles,
                }

        bbc3_config = self._parse_json(
            self._search_regex(
                r'(?s)bbcthreeConfig\s*=\s*({.+?})\s*;\s*<', webpage,
                'bbcthree config', default='{}'),
            playlist_id, transform_source=js_to_json, fatal=False) or {}
        payload = bbc3_config.get('payload') or {}
        if payload:
            clip = payload.get('currentClip') or {}
            clip_vpid = clip.get('vpid')
            clip_title = clip.get('title')
            if clip_vpid and clip_title:
                formats, subtitles = self._download_media_selector(clip_vpid)
                self._sort_formats(formats)
                return {
                    'id': clip_vpid,
                    'title': clip_title,
                    'thumbnail': dict_get(clip, ('poster', 'imageUrl')),
                    'description': clip.get('description'),
                    'duration': parse_duration(clip.get('duration')),
                    'formats': formats,
                    'subtitles': subtitles,
                }
            bbc3_playlist = try_get(
                payload, lambda x: x['content']['bbcMedia']['playlist'],
                dict)
            if bbc3_playlist:
                playlist_title = bbc3_playlist.get('title') or playlist_title
                thumbnail = bbc3_playlist.get('holdingImageURL')
                entries = []
                for bbc3_item in bbc3_playlist['items']:
                    programme_id = bbc3_item.get('versionID')
                    if not programme_id:
                        continue
                    formats, subtitles = self._download_media_selector(programme_id)
                    self._sort_formats(formats)
                    entries.append({
                        'id': programme_id,
                        'title': playlist_title,
                        'thumbnail': thumbnail,
                        'timestamp': timestamp,
                        'formats': formats,
                        'subtitles': subtitles,
                    })
                return self.playlist_result(
                    entries, playlist_id, playlist_title, playlist_description)

        initial_data = self._search_regex(
            r'window\.__INITIAL_DATA__\s*=\s*("{.+?}")\s*;', webpage,
            'quoted preload state', default=None)
        if initial_data is None:
            initial_data = self._search_regex(
                r'window\.__INITIAL_DATA__\s*=\s*({.+?})\s*;', webpage,
                'preload state', default={})
        else:
            initial_data = self._parse_json(initial_data or '"{}"', playlist_id, fatal=False)
        initial_data = self._parse_json(initial_data, playlist_id, fatal=False)
        if initial_data:
            def parse_media(media):
                if not media:
                    return
                for item in (try_get(media, lambda x: x['media']['items'], list) or []):
                    item_id = item.get('id')
                    item_title = item.get('title')
                    if not (item_id and item_title):
                        continue
                    formats, subtitles = self._download_media_selector(item_id)
                    self._sort_formats(formats)
                    item_desc = None
                    blocks = try_get(media, lambda x: x['summary']['blocks'], list)
                    if blocks:
                        summary = []
                        for block in blocks:
                            text = try_get(block, lambda x: x['model']['text'], compat_str)
                            if text:
                                summary.append(text)
                        if summary:
                            item_desc = '\n\n'.join(summary)
                    item_time = None
                    for meta in try_get(media, lambda x: x['metadata']['items'], list) or []:
                        if try_get(meta, lambda x: x['label']) == 'Published':
                            item_time = unified_timestamp(meta.get('timestamp'))
                            break
                    entries.append({
                        'id': item_id,
                        'title': item_title,
                        'thumbnail': item.get('holdingImageUrl'),
                        'formats': formats,
                        'subtitles': subtitles,
                        'timestamp': item_time,
                        'description': strip_or_none(item_desc),
                    })
            for resp in (initial_data.get('data') or {}).values():
                name = resp.get('name')
                if name == 'media-experience':
                    parse_media(try_get(resp, lambda x: x['data']['initialItem']['mediaItem'], dict))
                elif name == 'article':
                    for block in (try_get(resp,
                                          (lambda x: x['data']['blocks'],
                                           lambda x: x['data']['content']['model']['blocks'],),
                                          list) or []):
                        if block.get('type') != 'media':
                            continue
                        parse_media(block.get('model'))
            return self.playlist_result(
                entries, playlist_id, playlist_title, playlist_description)

        def extract_all(pattern):
            return list(filter(None, map(
                lambda s: self._parse_json(s, playlist_id, fatal=False),
                re.findall(pattern, webpage))))

        # Multiple video article (e.g.
        # http://www.bbc.co.uk/blogs/adamcurtis/entries/3662a707-0af9-3149-963f-47bea720b460)
        EMBED_URL = r'https?://(?:www\.)?bbc\.co\.uk/(?:[^/]+/)+%s(?:\b[^"]+)?' % self._ID_REGEX
        entries = []
        for match in extract_all(r'new\s+SMP\(({.+?})\)'):
            embed_url = match.get('playerSettings', {}).get('externalEmbedUrl')
            if embed_url and re.match(EMBED_URL, embed_url):
                entries.append(embed_url)
        entries.extend(re.findall(
            r'setPlaylist\("(%s)"\)' % EMBED_URL, webpage))
        if entries:
            return self.playlist_result(
                [self.url_result(entry_, 'BBCCoUk') for entry_ in entries],
                playlist_id, playlist_title, playlist_description)

        # Multiple video article (e.g. http://www.bbc.com/news/world-europe-32668511)
        medias = extract_all(r"data-media-meta='({[^']+})'")

        if not medias:
            # Single video article (e.g. http://www.bbc.com/news/video_and_audio/international)
            media_asset = self._search_regex(
                r'mediaAssetPage\.init\(\s*({.+?}), "/',
                webpage, 'media asset', default=None)
            if media_asset:
                media_asset_page = self._parse_json(media_asset, playlist_id, fatal=False)
                medias = []
                for video in media_asset_page.get('videos', {}).values():
                    medias.extend(video.values())

        if not medias:
            # Multiple video playlist with single `now playing` entry (e.g.
            # http://www.bbc.com/news/video_and_audio/must_see/33767813)
            vxp_playlist = self._parse_json(
                self._search_regex(
                    r'<script[^>]+class="vxp-playlist-data"[^>]+type="application/json"[^>]*>([^<]+)</script>',
                    webpage, 'playlist data'),
                playlist_id)
            playlist_medias = []
            for item in vxp_playlist:
                media = item.get('media')
                if not media:
                    continue
                playlist_medias.append(media)
                # Download single video if found media with asset id matching the video id from URL
                if item.get('advert', {}).get('assetId') == playlist_id:
                    medias = [media]
                    break
            # Fallback to the whole playlist
            if not medias:
                medias = playlist_medias

        entries = []
        for num, media_meta in enumerate(medias, start=1):
            formats, subtitles = self._extract_from_media_meta(media_meta, playlist_id)
            if not formats:
                continue
            self._sort_formats(formats)

            video_id = media_meta.get('externalId')
            if not video_id:
                video_id = playlist_id if len(medias) == 1 else '%s-%s' % (playlist_id, num)

            title = media_meta.get('caption')
            if not title:
                title = playlist_title if len(medias) == 1 else '%s - Video %s' % (playlist_title, num)

            duration = int_or_none(media_meta.get('durationInSeconds')) or parse_duration(media_meta.get('duration'))

            images = []
            for image in media_meta.get('images', {}).values():
                images.extend(image.values())
            if 'image' in media_meta:
                images.append(media_meta['image'])

            thumbnails = [{
                'url': image.get('href'),
                'width': int_or_none(image.get('width')),
                'height': int_or_none(image.get('height')),
            } for image in images]

            entries.append({
                'id': video_id,
                'title': title,
                'thumbnails': thumbnails,
                'duration': duration,
                'timestamp': timestamp,
                'formats': formats,
                'subtitles': subtitles,
            })

        return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)