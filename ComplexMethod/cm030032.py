def extractall(self, path=".", members=None, *, numeric_owner=False,
                   filter=None):
        """Extract all members from the archive to the current working
           directory and set owner, modification time and permissions on
           directories afterwards. 'path' specifies a different directory
           to extract to. 'members' is optional and must be a subset of the
           list returned by getmembers(). If 'numeric_owner' is True, only
           the numbers for user/group names are used and not the names.

           The 'filter' function will be called on each member just
           before extraction.
           It can return a changed TarInfo or None to skip the member.
           String names of common filters are accepted.
        """
        directories = []

        filter_function = self._get_filter_function(filter)
        if members is None:
            members = self

        for member in members:
            tarinfo, unfiltered = self._get_extract_tarinfo(
                member, filter_function, path)
            if tarinfo is None:
                continue
            if tarinfo.isdir():
                # For directories, delay setting attributes until later,
                # since permissions can interfere with extraction and
                # extracting contents can reset mtime.
                directories.append(unfiltered)
            self._extract_one(tarinfo, path, set_attrs=not tarinfo.isdir(),
                              numeric_owner=numeric_owner,
                              filter_function=filter_function)

        # Reverse sort directories.
        directories.sort(key=lambda a: a.name, reverse=True)


        # Set correct owner, mtime and filemode on directories.
        for unfiltered in directories:
            try:
                # Need to re-apply any filter, to take the *current* filesystem
                # state into account.
                try:
                    tarinfo = filter_function(unfiltered, path)
                except _FILTER_ERRORS as exc:
                    self._log_no_directory_fixup(unfiltered, repr(exc))
                    continue
                if tarinfo is None:
                    self._log_no_directory_fixup(unfiltered,
                                                 'excluded by filter')
                    continue
                dirpath = os.path.join(path, tarinfo.name)
                try:
                    lstat = os.lstat(dirpath)
                except FileNotFoundError:
                    self._log_no_directory_fixup(tarinfo, 'missing')
                    continue
                if not stat.S_ISDIR(lstat.st_mode):
                    # This is no longer a directory; presumably a later
                    # member overwrote the entry.
                    self._log_no_directory_fixup(tarinfo, 'not a directory')
                    continue
                self.chown(tarinfo, dirpath, numeric_owner=numeric_owner)
                self.utime(tarinfo, dirpath)
                self.chmod(tarinfo, dirpath)
            except ExtractError as e:
                self._handle_nonfatal_error(e)