def list(self, verbose=True, *, members=None):
        """Print a table of contents to sys.stdout. If 'verbose' is False, only
           the names of the members are printed. If it is True, an 'ls -l'-like
           output is produced. 'members' is optional and must be a subset of the
           list returned by getmembers().
        """
        # Convert tarinfo type to stat type.
        type2mode = {REGTYPE: stat.S_IFREG, SYMTYPE: stat.S_IFLNK,
                     FIFOTYPE: stat.S_IFIFO, CHRTYPE: stat.S_IFCHR,
                     DIRTYPE: stat.S_IFDIR, BLKTYPE: stat.S_IFBLK}
        self._check()

        if members is None:
            members = self
        for tarinfo in members:
            if verbose:
                if tarinfo.mode is None:
                    _safe_print("??????????")
                else:
                    modetype = type2mode.get(tarinfo.type, 0)
                    _safe_print(stat.filemode(modetype | tarinfo.mode))
                _safe_print("%s/%s" % (tarinfo.uname or tarinfo.uid,
                                       tarinfo.gname or tarinfo.gid))
                if tarinfo.ischr() or tarinfo.isblk():
                    _safe_print("%10s" %
                            ("%d,%d" % (tarinfo.devmajor, tarinfo.devminor)))
                else:
                    _safe_print("%10d" % tarinfo.size)
                if tarinfo.mtime is None:
                    _safe_print("????-??-?? ??:??:??")
                else:
                    _safe_print("%d-%02d-%02d %02d:%02d:%02d" \
                                % time.localtime(tarinfo.mtime)[:6])

            _safe_print(tarinfo.name + ("/" if tarinfo.isdir() else ""))

            if verbose:
                if tarinfo.issym():
                    _safe_print("-> " + tarinfo.linkname)
                if tarinfo.islnk():
                    _safe_print("link to " + tarinfo.linkname)
            print()