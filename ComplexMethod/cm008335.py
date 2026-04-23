def _download_playlist(self, playlist_id):
        try:
            playlist = self._download_json(
                f'http://www.bbc.co.uk/programmes/{playlist_id}/playlist.json',
                playlist_id, 'Downloading playlist JSON')
            formats = []
            subtitles = {}

            for version in playlist.get('allAvailableVersions', []):
                smp_config = version['smpConfig']
                title = smp_config['title']
                description = smp_config['summary']
                for item in smp_config['items']:
                    kind = item['kind']
                    if kind not in ('programme', 'radioProgramme'):
                        continue
                    programme_id = item.get('vpid')
                    duration = int_or_none(item.get('duration'))
                    version_formats, version_subtitles = self._download_media_selector(programme_id)
                    types = version['types']
                    for f in version_formats:
                        f['format_note'] = ', '.join(types)
                        if any('AudioDescribed' in x for x in types):
                            f['language_preference'] = -10
                    formats += version_formats
                    for tag, subformats in (version_subtitles or {}).items():
                        subtitles.setdefault(tag, []).extend(subformats)

            return programme_id, title, description, duration, formats, subtitles
        except ExtractorError as ee:
            if not (isinstance(ee.cause, HTTPError) and ee.cause.status == 404):
                raise

        # fallback to legacy playlist
        return self._process_legacy_playlist(playlist_id)