def _extract_member(self, tarinfo, targetpath, set_attrs=True,
                        numeric_owner=False, *, filter_function=None,
                        extraction_root=None):
        """Extract the filtered TarInfo object tarinfo to a physical
           file called targetpath.

           filter_function is only used when extracting a *different*
           member (e.g. as fallback to creating a symlink)
        """
        # Fetch the TarInfo object for the given name
        # and build the destination pathname, replacing
        # forward slashes to platform specific separators.
        targetpath = targetpath.rstrip("/")
        targetpath = targetpath.replace("/", os.sep)

        # Create all upper directories.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            # Create directories that are not part of the archive with
            # default permissions.
            os.makedirs(upperdirs, exist_ok=True)

        if tarinfo.islnk() or tarinfo.issym():
            self._dbg(1, "%s -> %s" % (tarinfo.name, tarinfo.linkname))
        else:
            self._dbg(1, tarinfo.name)

        if tarinfo.isreg():
            self.makefile(tarinfo, targetpath)
        elif tarinfo.isdir():
            self.makedir(tarinfo, targetpath)
        elif tarinfo.isfifo():
            self.makefifo(tarinfo, targetpath)
        elif tarinfo.ischr() or tarinfo.isblk():
            self.makedev(tarinfo, targetpath)
        elif tarinfo.islnk() or tarinfo.issym():
            self.makelink_with_filter(
                tarinfo, targetpath,
                filter_function=filter_function,
                extraction_root=extraction_root)
        elif tarinfo.type not in SUPPORTED_TYPES:
            self.makeunknown(tarinfo, targetpath)
        else:
            self.makefile(tarinfo, targetpath)

        if set_attrs:
            self.chown(tarinfo, targetpath, numeric_owner)
            if not tarinfo.issym():
                self.chmod(tarinfo, targetpath)
                self.utime(tarinfo, targetpath)