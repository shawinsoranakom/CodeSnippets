def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, urlh = self._download_embed_webpage_handle(
            video_id, headers=traverse_obj(parse_qs(url), {
                'Referer': ('embed_parent_url', -1),
                'Origin': ('embed_container_origin', -1)}))
        redirect_url = urlh.url
        if 'domain_not_allowed' in redirect_url:
            domain = traverse_obj(parse_qs(redirect_url), ('allowed_domains[]', ...), get_all=False)
            if not domain:
                raise ExtractorError(
                    'This is an embed-only presentation. Try passing --referer', expected=True)
            webpage, _ = self._download_embed_webpage_handle(video_id, headers={
                'Referer': f'https://{domain}/',
                'Origin': f'https://{domain}',
            })

        player_token = self._search_regex(r'data-player-token="([^"]+)"', webpage, 'player token')
        player_data = self._download_webpage(
            f'https://slideslive.com/player/{video_id}', video_id,
            note='Downloading player info', query={'player_token': player_token})
        player_info = self._extract_custom_m3u8_info(player_data)

        service_name = player_info['service_name'].lower()
        assert service_name in ('url', 'yoda', 'vimeo', 'youtube')
        service_id = player_info['service_id']

        slide_url_template = 'https://slides.slideslive.com/%s/slides/original/%s%s'
        slides, slides_info = {}, []

        if player_info.get('slides_json_url'):
            slides = self._download_json(
                player_info['slides_json_url'], video_id, fatal=False,
                note='Downloading slides JSON', errnote=False) or {}
            slide_ext_default = '.png'
            slide_quality = traverse_obj(slides, ('slide_qualities', 0))
            if slide_quality:
                slide_ext_default = '.jpg'
                slide_url_template = f'https://cdn.slideslive.com/data/presentations/%s/slides/{slide_quality}/%s%s'
            for slide_id, slide in enumerate(traverse_obj(slides, ('slides', ...), expected_type=dict), 1):
                slides_info.append((
                    slide_id, traverse_obj(slide, ('image', 'name')),
                    traverse_obj(slide, ('image', 'extname'), default=slide_ext_default),
                    int_or_none(slide.get('time'), scale=1000)))

        if not slides and player_info.get('slides_xml_url'):
            slides = self._download_xml(
                player_info['slides_xml_url'], video_id, fatal=False,
                note='Downloading slides XML', errnote='Failed to download slides info')
            if isinstance(slides, xml.etree.ElementTree.Element):
                slide_url_template = 'https://cdn.slideslive.com/data/presentations/%s/slides/big/%s%s'
                for slide_id, slide in enumerate(slides.findall('./slide')):
                    slides_info.append((
                        slide_id, xpath_text(slide, './slideName', 'name'), '.jpg',
                        int_or_none(xpath_text(slide, './timeSec', 'time'))))

        chapters, thumbnails = [], []
        if url_or_none(player_info.get('thumbnail')):
            thumbnails.append({'id': 'cover', 'url': player_info['thumbnail']})
        for slide_id, slide_path, slide_ext, start_time in slides_info:
            if slide_path:
                thumbnails.append({
                    'id': f'{slide_id:03d}',
                    'url': slide_url_template % (video_id, slide_path, slide_ext),
                })
            chapters.append({
                'title': f'Slide {slide_id:03d}',
                'start_time': start_time,
            })

        subtitles = {}
        for sub in traverse_obj(player_info, ('subtitles', ...), expected_type=dict):
            webvtt_url = url_or_none(sub.get('webvtt_url'))
            if not webvtt_url:
                continue
            subtitles.setdefault(sub.get('language') or 'en', []).append({
                'url': webvtt_url,
                'ext': 'vtt',
            })

        info = {
            'id': video_id,
            'title': player_info.get('title') or self._html_search_meta('title', webpage, default=''),
            'timestamp': unified_timestamp(player_info.get('timestamp')),
            'is_live': player_info.get('playlist_type') != 'vod',
            'thumbnails': thumbnails,
            'chapters': chapters,
            'subtitles': subtitles,
        }

        if service_name == 'url':
            info['url'] = service_id
        elif service_name == 'yoda':
            formats, duration = self._extract_formats_and_duration(
                player_info['video_servers'][0], service_id, video_id)
            info.update({
                'duration': duration,
                'formats': formats,
            })
        else:
            info.update({
                '_type': 'url_transparent',
                'url': service_id,
                'ie_key': service_name.capitalize(),
                'display_id': video_id,
            })
            if service_name == 'vimeo':
                info['url'] = smuggle_url(
                    f'https://player.vimeo.com/video/{service_id}',
                    {'referer': url})

        video_slides = traverse_obj(slides, ('slides', ..., 'video', 'id'))
        if not video_slides:
            return info

        def entries():
            yield info

            service_data = self._download_json(
                f'https://slideslive.com/player/{video_id}/slides_video_service_data',
                video_id, fatal=False, query={
                    'player_token': player_token,
                    'videos': ','.join(video_slides),
                }, note='Downloading video slides info', errnote='Failed to download video slides info') or {}

            for slide_id, slide in enumerate(traverse_obj(slides, ('slides', ...)), 1):
                if traverse_obj(slide, ('video', 'service')) != 'yoda':
                    continue
                video_path = traverse_obj(slide, ('video', 'id'))
                cdn_hostname = traverse_obj(service_data, (
                    video_path, 'video_servers', ...), get_all=False)
                if not cdn_hostname or not video_path:
                    continue
                formats, _ = self._extract_formats_and_duration(
                    cdn_hostname, video_path, video_id, skip_duration=True)
                if not formats:
                    continue
                yield {
                    'id': f'{video_id}-{slide_id:03d}',
                    'title': f'{info["title"]} - Slide {slide_id:03d}',
                    'timestamp': info['timestamp'],
                    'duration': int_or_none(traverse_obj(slide, ('video', 'duration_ms')), scale=1000),
                    'formats': formats,
                }

        return self.playlist_result(entries(), f'{video_id}-playlist', info['title'])