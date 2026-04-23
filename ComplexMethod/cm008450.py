def _extract_formats(self, content_id, slug):
        for retry in (False, True):
            try:
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    f'https://content.api.nebula.app/{content_id.split(":")[0]}s/{content_id}/manifest.m3u8',
                    slug, 'mp4', query={
                        'token': self._token,
                        'app_version': '23.10.0',
                        'platform': 'ios',
                    })
                break
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                    self.raise_login_required()
                if not retry and isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    self.to_screen('Reauthorizing with Nebula and retrying, because fetching video resulted in error')
                    self._real_initialize()
                    continue
                raise

        self.mark_watched(content_id, slug)
        return {'formats': fmts, 'subtitles': subs}