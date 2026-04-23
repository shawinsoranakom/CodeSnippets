def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace('skola.se/Produkter', 'play.se/program')
        webpage = self._download_webpage(url, video_id)
        urplayer_data = self._search_nextjs_data(webpage, video_id, fatal=False) or {}
        if urplayer_data:
            urplayer_data = traverse_obj(urplayer_data, ('props', 'pageProps', 'productData', {dict}))
            if not urplayer_data:
                raise ExtractorError('Unable to parse __NEXT_DATA__')
        else:
            accessible_episodes = self._parse_json(self._html_search_regex(
                r'data-react-class="routes/Product/components/ProgramContainer/ProgramContainer"[^>]+data-react-props="({.+?})"',
                webpage, 'urplayer data'), video_id)['accessibleEpisodes']
            urplayer_data = next(e for e in accessible_episodes if e.get('id') == int_or_none(video_id))
        episode = urplayer_data['title']
        sources = self._download_json(
            f'https://media-api.urplay.se/config-streaming/v1/urplay/sources/{video_id}', video_id,
            note='Downloading streaming information')
        hls_url = traverse_obj(sources, ('sources', 'hls', {url_or_none}, {require('HLS URL')}))
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, video_id, 'mp4', m3u8_id='hls')

        def parse_lang_code(code):
            "3-character language code or None (utils candidate)"
            if code is None:
                return
            lang = code.lower()
            if not ISO639Utils.long2short(lang):
                lang = ISO639Utils.short2long(lang)
            return lang or None

        for stream in urplayer_data['streamingInfo'].values():
            for k, v in stream.items():
                if (k in ('sd', 'hd') or not isinstance(v, dict)):
                    continue
                lang, sttl_url = (v.get(kk) for kk in ('language', 'location'))
                if not sttl_url:
                    continue
                lang = parse_lang_code(lang)
                if not lang:
                    continue
                sttl = subtitles.get(lang) or []
                sttl.append({'ext': k, 'url': sttl_url})
                subtitles[lang] = sttl

        image = urplayer_data.get('image') or {}
        thumbnails = []
        for k, v in image.items():
            t = {
                'id': k,
                'url': v,
            }
            wh = k.split('x')
            if len(wh) == 2:
                t.update({
                    'width': int_or_none(wh[0]),
                    'height': int_or_none(wh[1]),
                })
            thumbnails.append(t)

        series = urplayer_data.get('series') or {}
        series_title = dict_get(series, ('seriesTitle', 'title')) or dict_get(urplayer_data, ('seriesTitle', 'mainTitle'))

        return {
            'id': video_id,
            'title': f'{series_title} : {episode}' if series_title else episode,
            'description': urplayer_data.get('description'),
            'thumbnails': thumbnails,
            'timestamp': unified_timestamp(urplayer_data.get('publishedAt')),
            'series': series_title,
            'formats': formats,
            'duration': int_or_none(urplayer_data.get('duration')),
            'categories': urplayer_data.get('categories'),
            'tags': urplayer_data.get('keywords'),
            'season': series.get('label'),
            'episode': episode,
            'episode_number': int_or_none(urplayer_data.get('episodeNumber')),
            'age_limit': parse_age_limit(min(try_get(a, lambda x: x['from'], int) or 0
                                             for a in urplayer_data.get('ageRanges', []))),
            'subtitles': subtitles,
        }