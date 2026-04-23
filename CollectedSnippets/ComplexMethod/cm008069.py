def parse_graphql_video(video):
                    v_id = video.get('videoId') or video.get('id') or video_id
                    reel_info = traverse_obj(
                        video, ('creation_story', 'short_form_video_context', 'playback_video', {dict}))
                    if reel_info:
                        video = video['creation_story']
                        video['owner'] = traverse_obj(video, ('short_form_video_context', 'video_owner'))
                        video.update(reel_info)

                    formats = []
                    q = qualities(['sd', 'hd'])

                    # Legacy formats extraction
                    fmt_data = traverse_obj(video, ('videoDeliveryLegacyFields', {dict})) or video
                    for key, format_id in (('playable_url', 'sd'), ('playable_url_quality_hd', 'hd'),
                                           ('playable_url_dash', ''), ('browser_native_hd_url', 'hd'),
                                           ('browser_native_sd_url', 'sd')):
                        playable_url = fmt_data.get(key)
                        if not playable_url:
                            continue
                        if determine_ext(playable_url) == 'mpd':
                            formats.extend(self._extract_mpd_formats(playable_url, video_id, fatal=False))
                        else:
                            formats.append({
                                'format_id': format_id,
                                # sd, hd formats w/o resolution info should be deprioritized below DASH
                                'quality': q(format_id) - 3,
                                'url': playable_url,
                            })
                    extract_dash_manifest(fmt_data, formats)

                    # New videoDeliveryResponse formats extraction
                    fmt_data = traverse_obj(video, ('videoDeliveryResponseFragment', 'videoDeliveryResponseResult'))
                    mpd_urls = traverse_obj(fmt_data, ('dash_manifest_urls', ..., 'manifest_url', {url_or_none}))
                    dash_manifests = traverse_obj(fmt_data, ('dash_manifests', lambda _, v: v['manifest_xml']))
                    for idx, dash_manifest in enumerate(dash_manifests):
                        extract_dash_manifest(dash_manifest, formats, mpd_url=traverse_obj(mpd_urls, idx))
                    if not dash_manifests:
                        # Only extract from MPD URLs if the manifests are not already provided
                        for mpd_url in mpd_urls:
                            formats.extend(self._extract_mpd_formats(mpd_url, video_id, fatal=False))
                    for prog_fmt in traverse_obj(fmt_data, ('progressive_urls', lambda _, v: v['progressive_url'])):
                        format_id = traverse_obj(prog_fmt, ('metadata', 'quality', {str.lower}))
                        formats.append({
                            'format_id': format_id,
                            # sd, hd formats w/o resolution info should be deprioritized below DASH
                            'quality': q(format_id) - 3,
                            'url': prog_fmt['progressive_url'],
                        })
                    for m3u8_url in traverse_obj(fmt_data, ('hls_playlist_urls', ..., 'hls_playlist_url', {url_or_none})):
                        formats.extend(self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', fatal=False, m3u8_id='hls'))

                    if not formats:
                        # Do not append false positive entry w/o any formats
                        return

                    automatic_captions, subtitles = {}, {}
                    is_broadcast = traverse_obj(video, ('is_video_broadcast', {bool}))
                    for caption in traverse_obj(video, (
                        'video_available_captions_locales',
                        {lambda x: sorted(x, key=lambda c: c['locale'])},
                        lambda _, v: url_or_none(v['captions_url']),
                    )):
                        lang = caption.get('localized_language') or 'und'
                        subs = {
                            'url': caption['captions_url'],
                            'name': format_field(caption, 'localized_country', f'{lang} (%s)', default=lang),
                        }
                        if caption.get('localized_creation_method') or is_broadcast:
                            automatic_captions.setdefault(caption['locale'], []).append(subs)
                        else:
                            subtitles.setdefault(caption['locale'], []).append(subs)
                    captions_url = traverse_obj(video, ('captions_url', {url_or_none}))
                    if captions_url and not automatic_captions and not subtitles:
                        locale = self._html_search_meta(
                            ['og:locale', 'twitter:locale'], webpage, 'locale', default='en_US')
                        (automatic_captions if is_broadcast else subtitles)[locale] = [{'url': captions_url}]

                    info = {
                        'id': v_id,
                        'formats': formats,
                        'thumbnail': traverse_obj(
                            video, ('thumbnailImage', 'uri'), ('preferred_thumbnail', 'image', 'uri')),
                        'uploader_id': traverse_obj(video, ('owner', 'id', {str_or_none})),
                        'timestamp': traverse_obj(video, 'publish_time', 'creation_time', expected_type=int_or_none),
                        'duration': (float_or_none(video.get('playable_duration_in_ms'), 1000)
                                     or float_or_none(video.get('length_in_second'))),
                        'automatic_captions': automatic_captions,
                        'subtitles': subtitles,
                    }
                    process_formats(info)
                    description = try_get(video, lambda x: x['savable_description']['text'])
                    title = video.get('name')
                    if title:
                        info.update({
                            'title': title,
                            'description': description,
                        })
                    else:
                        info['title'] = description or f'Facebook video #{v_id}'
                    entries.append(info)