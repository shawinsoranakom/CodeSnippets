def add_path_info(self, kwargs):
        """
        for results that are files, supplement the info about the file
        in the return path with stats about the file path.
        """

        path = kwargs.get('path', kwargs.get('dest', None))
        if path is None:
            return kwargs
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if os.path.exists(b_path):
            (uid, gid) = self.user_and_group(path)
            kwargs['uid'] = uid
            kwargs['gid'] = gid
            try:
                user = pwd.getpwuid(uid)[0]
            except KeyError:
                user = str(uid)
            try:
                group = grp.getgrgid(gid)[0]
            except KeyError:
                group = str(gid)
            kwargs['owner'] = user
            kwargs['group'] = group
            st = os.lstat(b_path)
            kwargs['mode'] = '0%03o' % stat.S_IMODE(st[stat.ST_MODE])
            # secontext not yet supported
            if os.path.islink(b_path):
                kwargs['state'] = 'link'
            elif os.path.isdir(b_path):
                kwargs['state'] = 'directory'
            elif os.stat(b_path).st_nlink > 1:
                kwargs['state'] = 'hard'
            else:
                kwargs['state'] = 'file'
            if self.selinux_enabled():
                kwargs['secontext'] = ':'.join(self.selinux_context(path))
            kwargs['size'] = st[stat.ST_SIZE]
        return kwargs