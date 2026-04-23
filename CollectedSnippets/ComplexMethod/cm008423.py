def _real_extract(self, url):
        base, playlist_id, extra_id = self._match_valid_url(url).groups()

        program = self._download_json(
            f'{base}.json', playlist_id, 'Downloading program JSON')

        if extra_id:
            extra_id = extra_id.upper().rstrip('/')

        playlist_title = program.get('name')
        entries = []
        for b in (program.get('blocks') or []):
            for s in (b.get('sets') or []):
                if extra_id:
                    if extra_id != join_nonempty(
                            b.get('name'), s.get('name'), delim='/').replace(' ', '-').upper():
                        continue
                    playlist_title = join_nonempty(playlist_title, s.get('name'), delim=' - ')

                s_id = s.get('id')
                if not s_id:
                    continue
                medias = self._download_json(
                    f'{base}/{s_id}.json', s_id,
                    'Downloading content set JSON', fatal=False)
                if not medias:
                    continue
                for m in (medias.get('items') or []):
                    path_id = m.get('path_id')
                    if not path_id:
                        continue
                    video_url = urljoin(url, path_id)
                    entries.append(self.url_result(
                        video_url, ie=RaiPlayIE.ie_key(),
                        video_id=RaiPlayIE._match_id(video_url)))

        return self.playlist_result(
            entries, playlist_id, playlist_title,
            try_get(program, lambda x: x['program_info']['description']))