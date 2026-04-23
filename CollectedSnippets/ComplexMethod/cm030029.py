def gettarinfo(self, name=None, arcname=None, fileobj=None):
        """Create a TarInfo object from the result of os.stat or equivalent
           on an existing file. The file is either named by 'name', or
           specified as a file object 'fileobj' with a file descriptor. If
           given, 'arcname' specifies an alternative name for the file in the
           archive, otherwise, the name is taken from the 'name' attribute of
           'fileobj', or the 'name' argument. The name should be a text
           string.
        """
        self._check("awx")

        # When fileobj is given, replace name by
        # fileobj's real name.
        if fileobj is not None:
            name = fileobj.name

        # Building the name of the member in the archive.
        # Backward slashes are converted to forward slashes,
        # Absolute paths are turned to relative paths.
        if arcname is None:
            arcname = name
        drv, arcname = os.path.splitdrive(arcname)
        arcname = arcname.replace(os.sep, "/")
        arcname = arcname.lstrip("/")

        # Now, fill the TarInfo object with
        # information specific for the file.
        tarinfo = self.tarinfo()
        tarinfo._tarfile = self  # To be removed in 3.16.

        # Use os.stat or os.lstat, depending on if symlinks shall be resolved.
        if fileobj is None:
            if not self.dereference:
                statres = os.lstat(name)
            else:
                statres = os.stat(name)
        else:
            statres = os.fstat(fileobj.fileno())
        linkname = ""

        stmd = statres.st_mode
        if stat.S_ISREG(stmd):
            inode = (statres.st_ino, statres.st_dev)
            if not self.dereference and statres.st_nlink > 1 and \
                    inode in self.inodes and arcname != self.inodes[inode]:
                # Is it a hardlink to an already
                # archived file?
                type = LNKTYPE
                linkname = self.inodes[inode]
            else:
                # The inode is added only if its valid.
                # For win32 it is always 0.
                type = REGTYPE
                if inode[0]:
                    self.inodes[inode] = arcname
        elif stat.S_ISDIR(stmd):
            type = DIRTYPE
        elif stat.S_ISFIFO(stmd):
            type = FIFOTYPE
        elif stat.S_ISLNK(stmd):
            type = SYMTYPE
            linkname = os.readlink(name)
        elif stat.S_ISCHR(stmd):
            type = CHRTYPE
        elif stat.S_ISBLK(stmd):
            type = BLKTYPE
        else:
            return None

        # Fill the TarInfo object with all
        # information we can get.
        tarinfo.name = arcname
        tarinfo.mode = stmd
        tarinfo.uid = statres.st_uid
        tarinfo.gid = statres.st_gid
        if type == REGTYPE:
            tarinfo.size = statres.st_size
        else:
            tarinfo.size = 0
        tarinfo.mtime = statres.st_mtime
        tarinfo.type = type
        tarinfo.linkname = linkname

        # Calls to pwd.getpwuid() and grp.getgrgid() tend to be expensive. To
        # speed things up, cache the resolved usernames and group names.
        if pwd:
            if tarinfo.uid not in self._unames:
                try:
                    self._unames[tarinfo.uid] = pwd.getpwuid(tarinfo.uid)[0]
                except KeyError:
                    self._unames[tarinfo.uid] = ''
            tarinfo.uname = self._unames[tarinfo.uid]
        if grp:
            if tarinfo.gid not in self._gnames:
                try:
                    self._gnames[tarinfo.gid] = grp.getgrgid(tarinfo.gid)[0]
                except KeyError:
                    self._gnames[tarinfo.gid] = ''
            tarinfo.gname = self._gnames[tarinfo.gid]

        if type in (CHRTYPE, BLKTYPE):
            if hasattr(os, "major") and hasattr(os, "minor"):
                tarinfo.devmajor = os.major(statres.st_rdev)
                tarinfo.devminor = os.minor(statres.st_rdev)
        return tarinfo