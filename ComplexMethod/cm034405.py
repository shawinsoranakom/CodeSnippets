def create_user(self):
        cmd = [
            self.module.get_bin_path('pw', True),
            'useradd',
            '-n',
            self.name,
        ]

        if self.uid is not None:
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.comment is not None:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            cmd.append('-d')
            cmd.append(self.home)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            cmd.append('-g')
            cmd.append(self.group)

        if self.groups is not None:
            groups = self.get_groups_set()
            cmd.append('-G')
            cmd.append(','.join(groups))

        if self.create_home:
            cmd.append('-m')

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.shell is not None:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            cmd.append('-L')
            cmd.append(self.login_class)

        if self.expires is not None:
            cmd.append('-e')
            if self.expires < time.gmtime(0):
                cmd.append('0')
            else:
                cmd.append(str(calendar.timegm(self.expires)))

        if self.uid_min is not None:
            cmd.append('-K')
            cmd.append('UID_MIN=' + str(self.uid_min))

        if self.uid_max is not None:
            cmd.append('-K')
            cmd.append('UID_MAX=' + str(self.uid_max))

        # system cannot be handled currently - should we error if its requested?
        # create the user
        (rc, out, err) = self.execute_command(cmd)

        if rc is not None and rc != 0:
            self.module.fail_json(name=self.name, msg=err, rc=rc)

        # we have to set the password in a second command
        if self.password is not None:
            cmd = [
                self.module.get_bin_path('chpass', True),
                '-p',
                self.password,
                self.name
            ]
            _rc, _out, _err = self.execute_command(cmd)
            if rc is None:
                rc = _rc
            out += _out
            err += _err

        # we have to lock/unlock the password in a distinct command
        _rc, _out, _err = self._handle_lock()
        if rc is None:
            rc = _rc
        out += _out
        err += _err

        return (rc, out, err)