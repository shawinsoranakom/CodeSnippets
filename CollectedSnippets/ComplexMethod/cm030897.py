def add(self, name, *, type=None, symlink_to=None, hardlink_to=None,
            mode=None, size=None, content=None, **kwargs):
        """Add a member to the test archive. Call within `with`.

        Provides many shortcuts:
        - default `type` is based on symlink_to, hardlink_to, and trailing `/`
          in name (which is stripped)
        - size & content defaults are based on each other
        - content can be str or bytes
        - mode should be textual ('-rwxrwxrwx')

        (add more! this is unstable internal test-only API)
        """
        name = str(name)
        tarinfo = tarfile.TarInfo(name).replace(**kwargs)
        if content is not None:
            if isinstance(content, str):
                content = content.encode()
            size = len(content)
        if size is not None:
            tarinfo.size = size
            if content is None:
                content = bytes(tarinfo.size)
        if mode:
            tarinfo.mode = _filemode_to_int(mode)
        if symlink_to is not None:
            type = tarfile.SYMTYPE
            tarinfo.linkname = str(symlink_to)
        if hardlink_to is not None:
            type = tarfile.LNKTYPE
            tarinfo.linkname = str(hardlink_to)
        if name.endswith('/') and type is None:
            type = tarfile.DIRTYPE
        if type is not None:
            tarinfo.type = type
        if tarinfo.isreg():
            fileobj = io.BytesIO(content)
        else:
            fileobj = None
        self.tar_w.addfile(tarinfo, fileobj)