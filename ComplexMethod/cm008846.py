def __init__(self, ydl, info_dict):
        self.ydl = ydl

        # _entries must be assigned now since infodict can change during iteration
        entries = info_dict.get('entries')
        if entries is None:
            raise EntryNotInPlaylist('There are no entries')
        elif isinstance(entries, list):
            self.is_exhausted = True

        requested_entries = info_dict.get('requested_entries')
        self.is_incomplete = requested_entries is not None
        if self.is_incomplete:
            assert self.is_exhausted
            self._entries = [self.MissingEntry] * max(requested_entries or [0])
            for i, entry in zip(requested_entries, entries):  # noqa: B905
                self._entries[i - 1] = entry
        elif isinstance(entries, (list, PagedList, LazyList)):
            self._entries = entries
        else:
            self._entries = LazyList(entries)