def _real_extract(self, url):
        base, playlist_id, extra_id = self._match_valid_url(url).group('base', 'id', 'extra_id')
        url = f'{base}.json'
        program = self._download_json(url, playlist_id, 'Downloading program JSON')

        if extra_id:
            extra_id = extra_id.rstrip('/')
            playlist_id += '_' + extra_id.replace('/', '_')
            path = next(c['path_id'] for c in program.get('filters') or [] if extra_id in c.get('weblink'))
            program = self._download_json(
                urljoin('https://www.raiplaysound.it', path), playlist_id, 'Downloading program secondary JSON')

        entries = [
            self.url_result(urljoin(base, c['path_id']), ie=RaiPlaySoundIE.ie_key())
            for c in traverse_obj(program, 'cards', ('block', 'cards')) or []
            if c.get('path_id')]

        return self.playlist_result(entries, playlist_id, program.get('title'),
                                    traverse_obj(program, ('podcast_info', 'description')))