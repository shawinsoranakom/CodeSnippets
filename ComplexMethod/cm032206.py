def status(self, info_or_id, download_dir=None):
        """
        Return a constant describing the status of the given package
        or collection.  Status can be one of ``INSTALLED``,
        ``NOT_INSTALLED``, ``STALE``, or ``PARTIAL``.
        """
        if download_dir is None:
            download_dir = self._download_dir
        info = self._info_or_id(info_or_id)

        # Handle collections:
        if isinstance(info, Collection):
            pkg_status = [self.status(pkg.id) for pkg in info.packages]
            if self.STALE in pkg_status:
                return self.STALE
            elif self.PARTIAL in pkg_status:
                return self.PARTIAL
            elif self.INSTALLED in pkg_status and self.NOT_INSTALLED in pkg_status:
                return self.PARTIAL
            elif self.NOT_INSTALLED in pkg_status:
                return self.NOT_INSTALLED
            else:
                return self.INSTALLED

        # Handle packages:
        else:
            filepath = os.path.join(download_dir, info.filename)
            if download_dir != self._download_dir:
                return self._pkg_status(info, filepath)
            else:
                if info.id not in self._status_cache:
                    self._status_cache[info.id] = self._pkg_status(info, filepath)
                return self._status_cache[info.id]