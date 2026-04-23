def _real_extract(self, url):
        video_id, is_podcast = self._match_valid_url(url).group('id', 'podcast')
        json_ld = self._search_json_ld(self._download_webpage(url, video_id), video_id, default={})
        video_data = self._download_json(
            f'https://player.api.yle.fi/v1/preview/{video_id}.json?app_id=player_static_prod&app_key=8930d72170e48303cf5f3867780d549b',
            video_id, headers={
                'origin': 'https://areena.yle.fi',
                'referer': 'https://areena.yle.fi/',
                'content-type': 'application/json',
            })['data']

        # Example title: 'K1, J2: Pouchit | Modernit miehet'
        season_number, episode_number, episode, series = self._search_regex(
            r'K(?P<season_no>\d+),\s*J(?P<episode_no>\d+):?\s*\b(?P<episode>[^|]+)\s*|\s*(?P<series>.+)',
            json_ld.get('title') or '', 'episode metadata', group=('season_no', 'episode_no', 'episode', 'series'),
            default=(None, None, None, None))
        description = traverse_obj(video_data, ('ongoing_ondemand', 'description', 'fin', {str}))

        subtitles = {}
        for sub in traverse_obj(video_data, ('ongoing_ondemand', 'subtitles', lambda _, v: url_or_none(v['uri']))):
            subtitles.setdefault(sub.get('language') or 'und', []).append({
                'url': sub['uri'],
                'ext': 'srt',
                'name': sub.get('kind'),
            })

        info_dict, metadata = {}, {}
        if is_podcast and traverse_obj(video_data, ('ongoing_ondemand', 'media_url', {url_or_none})):
            metadata = video_data['ongoing_ondemand']
            info_dict['url'] = metadata['media_url']
        elif traverse_obj(video_data, ('ongoing_event', 'manifest_url', {url_or_none})):
            metadata = video_data['ongoing_event']
            metadata.pop('duration', None)  # Duration is not accurate for livestreams
            info_dict['live_status'] = 'is_live'
        elif traverse_obj(video_data, ('ongoing_ondemand', 'manifest_url', {url_or_none})):
            metadata = video_data['ongoing_ondemand']
        # XXX: Has all externally-hosted Kaltura content been moved to native hosting?
        elif kaltura_id := traverse_obj(video_data, ('ongoing_ondemand', 'kaltura', 'id', {str})):
            metadata = video_data['ongoing_ondemand']
            info_dict.update({
                '_type': 'url_transparent',
                'url': smuggle_url(f'kaltura:1955031:{kaltura_id}', {'source_url': url}),
                'ie_key': KalturaIE.ie_key(),
            })
        elif traverse_obj(video_data, ('gone', {dict})):
            self.raise_no_formats('The content is no longer available', expected=True, video_id=video_id)
            metadata = video_data['gone']
        else:
            raise ExtractorError('Unable to extract content')

        if not info_dict.get('url') and metadata.get('manifest_url'):
            info_dict['formats'], subs = self._extract_m3u8_formats_and_subtitles(
                metadata['manifest_url'], video_id, 'mp4', m3u8_id='hls')
            self._merge_subtitles(subs, target=subtitles)

        return {
            **traverse_obj(json_ld, {
                'title': 'title',
                'thumbnails': ('thumbnails', ..., {'url': 'url'}),
            }),
            'id': video_id,
            'title': episode,
            'description': description,
            'series': series,
            'season_number': (int_or_none(self._search_regex(r'Kausi (\d+)', description, 'season number', default=None))
                              or int_or_none(season_number)),
            'episode_number': int_or_none(episode_number),
            'subtitles': subtitles or None,
            **traverse_obj(metadata, {
                'title': ('title', 'fin', {str}),
                'description': ('description', 'fin', {str}),
                'series': ('series', 'title', 'fin', {str}),
                'episode_number': ('episode_number', {int_or_none}),
                'age_limit': ('content_rating', 'age_restriction', {int_or_none}),
                'release_timestamp': ('start_time', {parse_iso8601}),
                'duration': ('duration', 'duration_in_seconds', {int_or_none}),
            }),
            **info_dict,
        }