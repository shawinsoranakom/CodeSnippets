def _extract_from_legacy_playlist(self, playlist, playlist_id):
        no_items = playlist.find('./{%s}noItems' % self._EMP_PLAYLIST_NS)
        if no_items is not None:
            reason = no_items.get('reason')
            if reason == 'preAvailability':
                msg = 'Episode %s is not yet available' % playlist_id
            elif reason == 'postAvailability':
                msg = 'Episode %s is no longer available' % playlist_id
            elif reason == 'noMedia':
                msg = 'Episode %s is not currently available' % playlist_id
            else:
                msg = 'Episode %s is not available: %s' % (playlist_id, reason)
            raise ExtractorError(msg, expected=True)

        for item in self._extract_items(playlist):
            kind = item.get('kind')
            if kind not in ('programme', 'radioProgramme'):
                continue
            title = playlist.find('./{%s}title' % self._EMP_PLAYLIST_NS).text
            description_el = playlist.find('./{%s}summary' % self._EMP_PLAYLIST_NS)
            description = description_el.text if description_el is not None else None

            def get_programme_id(item):
                def get_from_attributes(item):
                    for p in ('identifier', 'group'):
                        value = item.get(p)
                        if value and re.match(r'^[pb][\da-z]{7}$', value):
                            return value
                get_from_attributes(item)
                mediator = item.find('./{%s}mediator' % self._EMP_PLAYLIST_NS)
                if mediator is not None:
                    return get_from_attributes(mediator)

            programme_id = get_programme_id(item)
            duration = int_or_none(item.get('duration'))

            if programme_id:
                formats, subtitles = self._download_media_selector(programme_id)
            else:
                formats, subtitles = self._process_media_selector(item, playlist_id)
                programme_id = playlist_id

        return programme_id, title, description, duration, formats, subtitles