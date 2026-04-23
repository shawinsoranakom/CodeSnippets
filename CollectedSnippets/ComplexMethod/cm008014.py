def __process_playlist(self, ie_result, download):
        """Process each entry in the playlist"""
        assert ie_result['_type'] in ('playlist', 'multi_video')

        common_info = self._playlist_infodict(ie_result, strict=True)
        title = common_info.get('playlist') or '<Untitled>'
        if self._match_entry(common_info, incomplete=True) is not None:
            return
        self.to_screen(f'[download] Downloading {ie_result["_type"]}: {title}')

        all_entries = PlaylistEntries(self, ie_result)
        entries = orderedSet(all_entries.get_requested_items(), lazy=True)

        lazy = self.params.get('lazy_playlist')
        if lazy:
            resolved_entries, n_entries = [], 'N/A'
            ie_result['requested_entries'], ie_result['entries'] = None, None
        else:
            entries = resolved_entries = list(entries)
            n_entries = len(resolved_entries)
            ie_result['requested_entries'], ie_result['entries'] = tuple(zip(*resolved_entries, strict=True)) or ([], [])
        if not ie_result.get('playlist_count'):
            # Better to do this after potentially exhausting entries
            ie_result['playlist_count'] = all_entries.get_full_count()

        extra = self._playlist_infodict(ie_result, n_entries=int_or_none(n_entries))
        ie_copy = collections.ChainMap(ie_result, extra)

        _infojson_written = False
        write_playlist_files = self.params.get('allow_playlist_files', True)
        if write_playlist_files and self.params.get('list_thumbnails'):
            self.list_thumbnails(ie_result)
        if write_playlist_files and not self.params.get('simulate'):
            _infojson_written = self._write_info_json(
                'playlist', ie_result, self.prepare_filename(ie_copy, 'pl_infojson'))
            if _infojson_written is None:
                return
            if self._write_description('playlist', ie_result,
                                       self.prepare_filename(ie_copy, 'pl_description')) is None:
                return
            # TODO: This should be passed to ThumbnailsConvertor if necessary
            self._write_thumbnails('playlist', ie_result, self.prepare_filename(ie_copy, 'pl_thumbnail'))

        if lazy:
            if self.params.get('playlistreverse') or self.params.get('playlistrandom'):
                self.report_warning('playlistreverse and playlistrandom are not supported with lazy_playlist', only_once=True)
        elif self.params.get('playlistreverse'):
            entries.reverse()
        elif self.params.get('playlistrandom'):
            random.shuffle(entries)

        self.to_screen(f'[{ie_result["extractor"]}] Playlist {title}: Downloading {n_entries} items'
                       f'{format_field(ie_result, "playlist_count", " of %s")}')

        keep_resolved_entries = self.params.get('extract_flat') != 'discard'
        if self.params.get('extract_flat') == 'discard_in_playlist':
            keep_resolved_entries = ie_result['_type'] != 'playlist'
        if keep_resolved_entries:
            self.write_debug('The information of all playlist entries will be held in memory')

        failures = 0
        max_failures = self.params.get('skip_playlist_after_errors') or float('inf')
        for i, (playlist_index, entry) in enumerate(entries):
            if lazy:
                resolved_entries.append((playlist_index, entry))
            if not entry:
                continue

            entry['__x_forwarded_for_ip'] = ie_result.get('__x_forwarded_for_ip')
            if not lazy and 'playlist-index' in self.params['compat_opts']:
                playlist_index = ie_result['requested_entries'][i]

            entry_copy = collections.ChainMap(entry, {
                **common_info,
                'n_entries': int_or_none(n_entries),
                'playlist_index': playlist_index,
                'playlist_autonumber': i + 1,
            })

            if self._match_entry(entry_copy, incomplete=True) is not None:
                # For compatabilty with youtube-dl. See https://github.com/yt-dlp/yt-dlp/issues/4369
                resolved_entries[i] = (playlist_index, NO_DEFAULT)
                continue

            self.to_screen(
                f'[download] Downloading item {self._format_screen(i + 1, self.Styles.ID)} '
                f'of {self._format_screen(n_entries, self.Styles.EMPHASIS)}')

            entry_result = self.__process_iterable_entry(entry, download, collections.ChainMap({
                'playlist_index': playlist_index,
                'playlist_autonumber': i + 1,
            }, extra))
            if not entry_result:
                failures += 1
            if failures >= max_failures:
                self.report_error(
                    f'Skipping the remaining entries in playlist "{title}" since {failures} items failed extraction')
                break
            if keep_resolved_entries:
                resolved_entries[i] = (playlist_index, entry_result)

        # Update with processed data
        ie_result['entries'] = [e for _, e in resolved_entries if e is not NO_DEFAULT]
        ie_result['requested_entries'] = [i for i, e in resolved_entries if e is not NO_DEFAULT]
        if ie_result['requested_entries'] == try_call(lambda: list(range(1, ie_result['playlist_count'] + 1))):
            # Do not set for full playlist
            ie_result.pop('requested_entries')

        # Write the updated info to json
        if _infojson_written is True and self._write_info_json(
                'updated playlist', ie_result,
                self.prepare_filename(ie_copy, 'pl_infojson'), overwrite=True) is None:
            return

        ie_result = self.run_all_pps('playlist', ie_result)
        self.to_screen(f'[download] Finished downloading playlist: {title}')
        return ie_result