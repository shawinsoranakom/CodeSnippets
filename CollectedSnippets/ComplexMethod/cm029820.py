def _refresh(self):
        """Update table of contents mapping."""
        # If it has been less than two seconds since the last _refresh() call,
        # we have to unconditionally re-read the mailbox just in case it has
        # been modified, because os.path.mtime() has a 2 sec resolution in the
        # most common worst case (FAT) and a 1 sec resolution typically.  This
        # results in a few unnecessary re-reads when _refresh() is called
        # multiple times in that interval, but once the clock ticks over, we
        # will only re-read as needed.  Because the filesystem might be being
        # served by an independent system with its own clock, we record and
        # compare with the mtimes from the filesystem.  Because the other
        # system's clock might be skewing relative to our clock, we add an
        # extra delta to our wait.  The default is one tenth second, but is an
        # instance variable and so can be adjusted if dealing with a
        # particularly skewed or irregular system.
        if time.time() - self._last_read > 2 + self._skewfactor:
            refresh = False
            for subdir in self._toc_mtimes:
                mtime = os.path.getmtime(self._paths[subdir])
                if mtime > self._toc_mtimes[subdir]:
                    refresh = True
                self._toc_mtimes[subdir] = mtime
            if not refresh:
                return
        # Refresh toc
        self._toc = {}
        for subdir in self._toc_mtimes:
            path = self._paths[subdir]
            for entry in os.listdir(path):
                if entry.startswith('.'):
                    continue
                p = os.path.join(path, entry)
                if os.path.isdir(p):
                    continue
                uniq = entry.split(self.colon)[0]
                self._toc[uniq] = os.path.join(subdir, entry)
        self._last_read = time.time()