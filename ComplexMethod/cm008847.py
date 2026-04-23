def get_requested_items(self):
        playlist_items = self.ydl.params.get('playlist_items')
        playlist_start = self.ydl.params.get('playliststart', 1)
        playlist_end = self.ydl.params.get('playlistend')
        # For backwards compatibility, interpret -1 as whole list
        if playlist_end in (-1, None):
            playlist_end = ''
        if not playlist_items:
            playlist_items = f'{playlist_start}:{playlist_end}'
        elif playlist_start != 1 or playlist_end:
            self.ydl.report_warning('Ignoring playliststart and playlistend because playlistitems was given', only_once=True)

        for index in self.parse_playlist_items(playlist_items):
            for i, entry in self[index]:
                yield i, entry
                if not entry:
                    continue
                try:
                    # The item may have just been added to archive. Don't break due to it
                    if not self.ydl.params.get('lazy_playlist'):
                        # TODO: Add auto-generated fields
                        self.ydl._match_entry(entry, incomplete=True, silent=True)
                except (ExistingVideoReached, RejectedVideoReached):
                    return