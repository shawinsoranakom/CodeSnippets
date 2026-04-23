def __process_playlist(self, ie_result, download):
        # We process each entry in the playlist
        playlist = ie_result.get('title') or ie_result.get('id')

        self.to_screen('[download] Downloading playlist: %s' % playlist)

        playlist_results = []

        playliststart = self.params.get('playliststart', 1) - 1
        playlistend = self.params.get('playlistend')
        # For backwards compatibility, interpret -1 as whole list
        if playlistend == -1:
            playlistend = None

        playlistitems_str = self.params.get('playlist_items')
        playlistitems = None
        if playlistitems_str is not None:
            def iter_playlistitems(format):
                for string_segment in format.split(','):
                    if '-' in string_segment:
                        start, end = string_segment.split('-')
                        for item in range(int(start), int(end) + 1):
                            yield int(item)
                    else:
                        yield int(string_segment)
            playlistitems = orderedSet(iter_playlistitems(playlistitems_str))

        ie_entries = ie_result['entries']

        def make_playlistitems_entries(list_ie_entries):
            num_entries = len(list_ie_entries)
            return [
                list_ie_entries[i - 1] for i in playlistitems
                if -num_entries <= i - 1 < num_entries]

        def report_download(num_entries):
            self.to_screen(
                '[%s] playlist %s: Downloading %d videos' %
                (ie_result['extractor'], playlist, num_entries))

        if isinstance(ie_entries, list):
            n_all_entries = len(ie_entries)
            if playlistitems:
                entries = make_playlistitems_entries(ie_entries)
            else:
                entries = ie_entries[playliststart:playlistend]
            n_entries = len(entries)
            self.to_screen(
                '[%s] playlist %s: Collected %d video ids (downloading %d of them)' %
                (ie_result['extractor'], playlist, n_all_entries, n_entries))
        elif isinstance(ie_entries, PagedList):
            if playlistitems:
                entries = []
                for item in playlistitems:
                    entries.extend(ie_entries.getslice(
                        item - 1, item
                    ))
            else:
                entries = ie_entries.getslice(
                    playliststart, playlistend)
            n_entries = len(entries)
            report_download(n_entries)
        else:  # iterable
            if playlistitems:
                entries = make_playlistitems_entries(list(itertools.islice(
                    ie_entries, 0, max(playlistitems))))
            else:
                entries = list(itertools.islice(
                    ie_entries, playliststart, playlistend))
            n_entries = len(entries)
            report_download(n_entries)

        if self.params.get('playlistreverse', False):
            entries = entries[::-1]

        if self.params.get('playlistrandom', False):
            random.shuffle(entries)

        x_forwarded_for = ie_result.get('__x_forwarded_for_ip')

        for i, entry in enumerate(entries, 1):
            self.to_screen('[download] Downloading video %s of %s' % (i, n_entries))
            # This __x_forwarded_for_ip thing is a bit ugly but requires
            # minimal changes
            if x_forwarded_for:
                entry['__x_forwarded_for_ip'] = x_forwarded_for
            extra = {
                'n_entries': n_entries,
                'playlist': playlist,
                'playlist_id': ie_result.get('id'),
                'playlist_title': ie_result.get('title'),
                'playlist_uploader': ie_result.get('uploader'),
                'playlist_uploader_id': ie_result.get('uploader_id'),
                'playlist_index': playlistitems[i - 1] if playlistitems else i + playliststart,
                'extractor': ie_result['extractor'],
                'webpage_url': ie_result['webpage_url'],
                'webpage_url_basename': url_basename(ie_result['webpage_url']),
                'extractor_key': ie_result['extractor_key'],
            }

            reason = self._match_entry(entry, incomplete=True)
            if reason is not None:
                self.to_screen('[download] ' + reason)
                continue

            entry_result = self.__process_iterable_entry(entry, download, extra)
            # TODO: skip failed (empty) entries?
            playlist_results.append(entry_result)
        ie_result['entries'] = playlist_results
        self.to_screen('[download] Finished downloading playlist: %s' % playlist)
        return ie_result