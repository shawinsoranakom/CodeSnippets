def flush(self):
        """Write any pending changes to disk."""
        if not self._pending:
            if self._pending_sync:
                # Messages have only been added, so syncing the file
                # is enough.
                _sync_flush(self._file)
                self._pending_sync = False
            return

        # In order to be writing anything out at all, self._toc must
        # already have been generated (and presumably has been modified
        # by adding or deleting an item).
        assert self._toc is not None

        # Check length of self._file; if it's changed, some other process
        # has modified the mailbox since we scanned it.
        self._file.seek(0, 2)
        cur_len = self._file.tell()
        if cur_len != self._file_length:
            raise ExternalClashError('Size of mailbox file changed '
                                     '(expected %i, found %i)' %
                                     (self._file_length, cur_len))

        new_file = _create_temporary(self._path)
        try:
            new_toc = {}
            self._pre_mailbox_hook(new_file)
            for key in sorted(self._toc.keys()):
                start, stop = self._toc[key]
                self._file.seek(start)
                self._pre_message_hook(new_file)
                new_start = new_file.tell()
                while True:
                    buffer = self._file.read(min(4096,
                                                 stop - self._file.tell()))
                    if not buffer:
                        break
                    new_file.write(buffer)
                new_toc[key] = (new_start, new_file.tell())
                self._post_message_hook(new_file)
            self._file_length = new_file.tell()
        except:
            new_file.close()
            os.remove(new_file.name)
            raise
        _sync_close(new_file)
        # self._file is about to get replaced, so no need to sync.
        self._file.close()
        # Make sure the new file's mode and owner are the same as the old file's
        info = os.stat(self._path)
        os.chmod(new_file.name, info.st_mode)
        try:
            os.chown(new_file.name, info.st_uid, info.st_gid)
        except (AttributeError, OSError):
            pass
        try:
            os.rename(new_file.name, self._path)
        except FileExistsError:
            os.remove(self._path)
            os.rename(new_file.name, self._path)
        self._file = open(self._path, 'rb+')
        self._toc = new_toc
        self._pending = False
        self._pending_sync = False
        if self._locked:
            _lock_file(self._file, dotlock=False)