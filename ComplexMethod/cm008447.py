def _real_extract(self, url):
        display_id, series_id = self._match_valid_url(url).group('id', 'series_id')
        program = self._download_json(
            'https://www.ruv.is/gql/', display_id, query={'query': '''{
                Program(id: %s){
                    title image description short_description
                    episodes(id: {value: "%s"}) {
                        rating title duration file image firstrun description
                        clips {
                            time text
                        }
                        subtitles {
                            name value
                        }
                    }
                }
            }''' % (series_id, display_id)})['data']['Program']  # noqa: UP031
        episode = program['episodes'][0]

        subs = {}
        for trk in episode.get('subtitles'):
            if trk.get('name') and trk.get('value'):
                subs.setdefault(trk['name'], []).append({'url': trk['value'], 'ext': 'vtt'})

        media_url = episode['file']
        if determine_ext(media_url) == 'm3u8':
            formats = self._extract_m3u8_formats(media_url, display_id)
        else:
            formats = [{'url': media_url}]

        clips = [
            {'start_time': parse_duration(c.get('time')), 'title': c.get('text')}
            for c in episode.get('clips') or []]

        return {
            'id': display_id,
            'title': traverse_obj(program, ('episodes', 0, 'title'), 'title'),
            'description': traverse_obj(
                program, ('episodes', 0, 'description'), 'description', 'short_description',
                expected_type=lambda x: x or None),
            'subtitles': subs,
            'thumbnail': episode.get('image', '').replace('$$IMAGESIZE$$', '1960') or None,
            'timestamp': unified_timestamp(episode.get('firstrun')),
            'formats': formats,
            'age_limit': episode.get('rating'),
            'chapters': clips,
        }