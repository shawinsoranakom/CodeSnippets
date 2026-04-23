def _extract_formats(self, entry, audio_id):
        formats = []
        for audio in traverse_obj(entry, ('audioLinks', lambda _, v: url_or_none(v['url']))):
            ext = audio.get('variant')
            for retry in self.RetryManager():
                if retry.attempt > 1:
                    self._sleep(1, audio_id)
                try:
                    if ext == 'dash':
                        formats.extend(self._extract_mpd_formats(
                            audio['url'], audio_id, mpd_id=ext))
                    elif ext == 'hls':
                        formats.extend(self._extract_m3u8_formats(
                            audio['url'], audio_id, 'm4a', m3u8_id=ext))
                    else:
                        formats.append({
                            'url': audio['url'],
                            'ext': ext,
                            'format_id': ext,
                            'abr': int_or_none(audio.get('bitrate')),
                            'acodec': ext,
                            'vcodec': 'none',
                        })
                except ExtractorError as e:
                    if isinstance(e.cause, HTTPError) and e.cause.status == 429:
                        retry.error = e.cause
                    else:
                        self.report_warning(e.msg)

        return formats