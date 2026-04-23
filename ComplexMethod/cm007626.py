def _real_extract(self, url):
        base, playlist_id = re.match(self._VALID_URL, url).groups()

        program = self._download_json(
            base + '.json', playlist_id, 'Downloading program JSON')

        entries = []
        for b in (program.get('blocks') or []):
            for s in (b.get('sets') or []):
                s_id = s.get('id')
                if not s_id:
                    continue
                medias = self._download_json(
                    '%s/%s.json' % (base, s_id), s_id,
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
            entries, playlist_id, program.get('name'),
            try_get(program, lambda x: x['program_info']['description']))