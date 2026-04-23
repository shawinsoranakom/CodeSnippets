def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        json_ld_info = self._search_json_ld(webpage, playlist_id, default={})
        timestamp = json_ld_info.get('timestamp')

        playlist_title = json_ld_info.get('title') or re.sub(
            r'(.+)\s*-\s*BBC.*?$', r'\1', self._generic_title('', webpage, default='')).strip() or None

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
                                playlist_url = playlist.get(f'{key}Url')
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
                                    if isinstance(e.cause, HTTPError) and e.cause.status == 500:
                                        continue
                                    raise
                            if entry:
                                entries.append(entry)

        if entries:
            return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)

        # http://www.bbc.co.uk/learningenglish/chinese/features/lingohack/ep-181227
        group_id = self._search_regex(
            rf'<div[^>]+\bclass=["\']video["\'][^>]+\bdata-pid=["\']({self._ID_REGEX})',
            webpage, 'group id', default=None)
        if group_id:
            return self.url_result(
                f'https://www.bbc.co.uk/programmes/{group_id}', BBCCoUkIE)

        # single video story (e.g. http://www.bbc.com/travel/story/20150625-sri-lankas-spicy-secret)
        programme_id = self._search_regex(
            [rf'data-(?:video-player|media)-vpid="({self._ID_REGEX})"',
             rf'<param[^>]+name="externalIdentifier"[^>]+value="({self._ID_REGEX})"',
             rf'videoId\s*:\s*["\']({self._ID_REGEX})["\']'],
            webpage, 'vpid', default=None)

        if programme_id:
            formats, subtitles = self._download_media_selector(programme_id)
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
        # Several setPayload calls may be present but the video(s)
        # should be in one that mentions leadMedia or videoData
        morph_payload = self._search_json(
            r'\bMorph\s*\.\s*setPayload\s*\([^,]+,', webpage, 'morph payload', playlist_id,
            contains_pattern=r'{(?s:(?:(?!</script>).)+(?:"leadMedia"|\\"videoData\\")\s*:.+)}',
            default={})
        if morph_payload:
            for lead_media in traverse_obj(morph_payload, (
                    'body', 'components', ..., 'props', 'leadMedia', {dict})):
                programme_id = traverse_obj(lead_media, ('identifiers', ('vpid', 'playablePid'), {str}, any))
                if not programme_id:
                    continue
                formats, subtitles = self._download_media_selector(programme_id)
                return {
                    'id': programme_id,
                    'title': lead_media.get('title') or self._og_search_title(webpage),
                    **traverse_obj(lead_media, {
                        'description': ('summary', {str}),
                        'duration': ('duration', ('rawDuration', 'formattedDuration', 'spokenDuration'), {parse_duration}),
                        'uploader': ('masterBrand', {str}),
                        'uploader_id': ('mid', {str}),
                    }),
                    'formats': formats,
                    'subtitles': subtitles,
                }
            body = self._parse_json(traverse_obj(morph_payload, (
                'body', 'content', 'article', 'body')), playlist_id, fatal=False)
            for video_data in traverse_obj(body, (lambda _, v: v['videoData']['pid'], 'videoData')):
                if video_data.get('vpid'):
                    video_id = video_data['vpid']
                    formats, subtitles = self._download_media_selector(video_id)
                    entry = {
                        'id': video_id,
                        'formats': formats,
                        'subtitles': subtitles,
                    }
                else:
                    video_id = video_data['pid']
                    entry = self.url_result(
                        f'https://www.bbc.co.uk/programmes/{video_id}', BBCCoUkIE,
                        video_id, url_transparent=True)
                entry.update({
                    'timestamp': traverse_obj(morph_payload, (
                        'body', 'content', 'article', 'dateTimeInfo', 'dateTime', {parse_iso8601}),
                    ),
                    **traverse_obj(video_data, {
                        'thumbnail': (('iChefImage', 'image'), {url_or_none}, any),
                        'title': (('title', 'caption'), {str}, any),
                        'duration': ('duration', {parse_duration}),
                    }),
                })
                if video_data.get('isLead') and not self._yes_playlist(playlist_id, video_id):
                    return entry
                entries.append(entry)
            if entries:
                playlist_title = traverse_obj(morph_payload, (
                    'body', 'content', 'article', 'headline', {str})) or playlist_title
                return self.playlist_result(
                    entries, playlist_id, playlist_title, playlist_description)

        # various PRELOADED_STATE JSON
        preload_state = self._search_json(
            r'window\.__(?:PWA_)?PRELOADED_STATE__\s*=', webpage,
            'preload state', playlist_id, transform_source=js_to_json, default={})
        # PRELOADED_STATE with current programmme
        current_programme = traverse_obj(preload_state, ('programmes', 'current', {dict}))
        programme_id = traverse_obj(current_programme, ('id', {str}))
        if programme_id and current_programme.get('type') == 'playable_item':
            title = traverse_obj(current_programme, ('titles', ('tertiary', 'secondary'), {str}, any)) or playlist_title
            formats, subtitles = self._download_media_selector(programme_id)
            return {
                'id': programme_id,
                'title': title,
                'formats': formats,
                **traverse_obj(current_programme, {
                    'description': ('synopses', ('long', 'medium', 'short'), {str}, any),
                    'thumbnail': ('image_url', {lambda u: url_or_none(u.replace('{recipe}', 'raw'))}),
                    'duration': ('duration', 'value', {int_or_none}),
                    'uploader': ('network', 'short_title', {str}),
                    'uploader_id': ('network', 'id', {str}),
                    'timestamp': ((('availability', 'from'), ('release', 'date')), {parse_iso8601}, any),
                    'series': ('titles', 'primary', {str}),
                }),
                'subtitles': subtitles,
                'chapters': traverse_obj(preload_state, (
                    'tracklist', 'tracks', lambda _, v: float(v['offset']['start']), {
                        'title': ('titles', {lambda x: join_nonempty(
                            'primary', 'secondary', 'tertiary', delim=' - ', from_dict=x)}),
                        'start_time': ('offset', 'start', {float_or_none}),
                        'end_time': ('offset', 'end', {float_or_none}),
                    }),
                ),
            }

        # PWA_PRELOADED_STATE with article video asset
        asset_id = traverse_obj(preload_state, (
            'entities', 'articles', lambda k, _: k.rsplit('/', 1)[-1] == playlist_id,
            'assetVideo', 0, {str}, any))
        if asset_id:
            video_id = traverse_obj(preload_state, ('entities', 'videos', asset_id, 'vpid', {str}))
            if video_id:
                article = traverse_obj(preload_state, (
                    'entities', 'articles', lambda _, v: v['assetVideo'][0] == asset_id, any))

                def image_url(image_id):
                    return traverse_obj(preload_state, (
                        'entities', 'images', image_id, 'url',
                        {lambda u: url_or_none(u.replace('$recipe', 'raw'))}))

                formats, subtitles = self._download_media_selector(video_id)
                return {
                    'id': video_id,
                    **traverse_obj(preload_state, ('entities', 'videos', asset_id, {
                        'title': ('title', {str}),
                        'description': (('synopsisLong', 'synopsisMedium', 'synopsisShort'), {str}, any),
                        'thumbnail': (0, {image_url}),
                        'duration': ('duration', {int_or_none}),
                    })),
                    'formats': formats,
                    'subtitles': subtitles,
                    'timestamp': traverse_obj(article, ('displayDate', {parse_iso8601})),
                }
            else:
                return self.url_result(
                    f'https://www.bbc.co.uk/programmes/{asset_id}', BBCCoUkIE,
                    asset_id, playlist_title, display_id=playlist_id,
                    description=playlist_description)

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

        def parse_model(model):
            """Extract single video from model structure"""
            item_id = traverse_obj(model, ('versions', 0, 'versionId', {str}))
            if not item_id:
                return
            formats, subtitles = self._download_media_selector(item_id)
            return {
                'id': item_id,
                'formats': formats,
                'subtitles': subtitles,
                **traverse_obj(model, {
                    'title': ('title', {str}),
                    'thumbnail': ('imageUrl', {lambda u: urljoin(url, u.replace('$recipe', 'raw'))}),
                    'description': ('synopses', ('long', 'medium', 'short'), {str}, filter, any),
                    'duration': ('versions', 0, 'duration', {int}),
                    'timestamp': ('versions', 0, 'availableFrom', {int_or_none(scale=1000)}),
                }),
            }

        def is_type(*types):
            return lambda _, v: v['type'] in types

        initial_data = self._search_regex(
            r'window\.__INITIAL_DATA__\s*=\s*("{.+?}")\s*;', webpage,
            'quoted preload state', default=None)
        if initial_data is None:
            initial_data = self._search_regex(
                r'window\.__INITIAL_DATA__\s*=\s*({.+?})\s*;', webpage,
                'preload state', default='{}')
        else:
            initial_data = self._parse_json(initial_data or '"{}"', playlist_id, fatal=False)
        initial_data = self._parse_json(initial_data, playlist_id, fatal=False)
        if initial_data:
            for video_data in traverse_obj(initial_data, (
                    'stores', 'article', 'articleBodyContent', is_type('video'))):
                model = traverse_obj(video_data, (
                    'model', 'blocks', is_type('aresMedia'),
                    'model', 'blocks', is_type('aresMediaMetadata'),
                    'model', {dict}, any))
                entry = parse_model(model)
                if entry:
                    entries.append(entry)
            if entries:
                return self.playlist_result(
                    entries, playlist_id, playlist_title, playlist_description)

            def parse_media(media):
                if not media:
                    return
                for item in (try_get(media, lambda x: x['media']['items'], list) or []):
                    item_id = item.get('id')
                    item_title = item.get('title')
                    if not (item_id and item_title):
                        continue
                    formats, subtitles = self._download_media_selector(item_id)
                    item_desc = None
                    blocks = try_get(media, lambda x: x['summary']['blocks'], list)
                    if blocks:
                        summary = []
                        for block in blocks:
                            text = try_get(block, lambda x: x['model']['text'], str)
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
                        'duration': int_or_none(item.get('duration')),
                    })

            for resp in traverse_obj(initial_data, ('data', lambda _, v: v['name'])):
                name = resp['name']
                if name == 'media-experience':
                    parse_media(try_get(resp, lambda x: x['data']['initialItem']['mediaItem'], dict))
                elif name == 'article':
                    for block in traverse_obj(resp, (
                            'data', (None, ('content', 'model')), 'blocks',
                            is_type('media', 'video'), 'model', {dict})):
                        parse_media(block)
            return self.playlist_result(
                entries, playlist_id, playlist_title, playlist_description)

        # extract from SIMORGH_DATA hydration JSON
        simorgh_data = self._search_json(
            r'window\s*\.\s*SIMORGH_DATA\s*=', webpage,
            'simorgh data', playlist_id, default={})
        if simorgh_data:
            done = False
            for video_data in traverse_obj(simorgh_data, (
                    'pageData', 'content', 'model', 'blocks', is_type('video', 'legacyMedia'))):
                model = traverse_obj(video_data, (
                    'model', 'blocks', is_type('aresMedia'),
                    'model', 'blocks', is_type('aresMediaMetadata'),
                    'model', {dict}, any))
                if video_data['type'] == 'video':
                    entry = parse_model(model)
                else:  # legacyMedia: no duration, subtitles
                    block_id, entry = traverse_obj(model, ('blockId', {str})), None
                    media_data = traverse_obj(simorgh_data, (
                        'pageData', 'promo', 'media',
                        {lambda x: x if x['id'] == block_id else None}))
                    formats = traverse_obj(media_data, ('playlist', lambda _, v: url_or_none(v['url']), {
                        'url': ('url', {url_or_none}),
                        'ext': ('format', {str}),
                        'tbr': ('bitrate', {int_or_none(scale=1000)}),
                    }))
                    if formats:
                        entry = {
                            'id': block_id,
                            'display_id': playlist_id,
                            'formats': formats,
                            'description': traverse_obj(simorgh_data, ('pageData', 'promo', 'summary', {str})),
                            **traverse_obj(model, {
                                'title': ('title', {str}),
                                'thumbnail': ('imageUrl', {lambda u: urljoin(url, u.replace('$recipe', 'raw'))}),
                                'description': ('synopses', ('long', 'medium', 'short'), {str}, any),
                                'timestamp': ('firstPublished', {int_or_none(scale=1000)}),
                            }),
                        }
                        done = True
                if entry:
                    entries.append(entry)
                if done:
                    break
            if entries:
                return self.playlist_result(
                    entries, playlist_id, playlist_title, playlist_description)

        def extract_all(pattern):
            return list(filter(None, (
                self._parse_json(s, playlist_id, fatal=False)
                for s in re.findall(pattern, webpage))))

        # US accessed article with single embedded video (e.g.
        # https://www.bbc.com/news/uk-68546268)
        next_data = traverse_obj(self._search_nextjs_data(webpage, playlist_id, default={}),
                                 ('props', 'pageProps', 'page'))
        model = traverse_obj(next_data, (
            ..., 'contents', is_type('video'),
            'model', 'blocks', is_type('media'),
            'model', 'blocks', is_type('mediaMetadata'),
            'model', {dict}, any))
        if model and (entry := parse_model(model)):
            if not entry.get('timestamp'):
                entry['timestamp'] = traverse_obj(next_data, (
                    ..., 'contents', is_type('timestamp'), 'model',
                    'timestamp', {int_or_none(scale=1000)}, any))
            entries.append(entry)
            return self.playlist_result(
                entries, playlist_id, playlist_title, playlist_description)

        # Multiple video article (e.g.
        # http://www.bbc.co.uk/blogs/adamcurtis/entries/3662a707-0af9-3149-963f-47bea720b460)
        EMBED_URL = rf'https?://(?:www\.)?bbc\.co\.uk/(?:[^/]+/)+{self._ID_REGEX}(?:\b[^"]+)?'
        entries = []
        for match in extract_all(r'new\s+SMP\(({.+?})\)'):
            embed_url = match.get('playerSettings', {}).get('externalEmbedUrl')
            if embed_url and re.match(EMBED_URL, embed_url):
                entries.append(embed_url)
        entries.extend(re.findall(
            rf'setPlaylist\("({EMBED_URL})"\)', webpage))
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
            if not formats and not self.get_param('ignore_no_formats'):
                continue

            video_id = media_meta.get('externalId')
            if not video_id:
                video_id = playlist_id if len(medias) == 1 else f'{playlist_id}-{num}'

            title = media_meta.get('caption')
            if not title:
                title = playlist_title if len(medias) == 1 else f'{playlist_title} - Video {num}'

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