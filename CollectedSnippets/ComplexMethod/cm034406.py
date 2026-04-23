def modify_user(self):
        cmd = [
            self.module.get_bin_path('pw', True),
            'usermod',
            '-n',
            self.name
        ]
        cmd_len = len(cmd)
        info = self.user_info()

        if self.uid is not None and info[2] != int(self.uid):
            cmd.append('-u')
            cmd.append(self.uid)

            if self.non_unique:
                cmd.append('-o')

        if self.comment is not None and info[4] != self.comment:
            cmd.append('-c')
            cmd.append(self.comment)

        if self.home is not None:
            # Skip home creation for placeholder directories (e.g., /nonexistent, /dev/null)
            # These are conventions for system accounts and should not be created on disk
            if (info[5] != self.home and self.move_home) or (info[5] not in PLACEHOLDER_HOME_DIRS and not os.path.exists(self.home) and self.create_home):
                cmd.append('-m')
            if info[5] != self.home:
                cmd.append('-d')
                cmd.append(self.home)

            if self.skeleton is not None:
                cmd.append('-k')
                cmd.append(self.skeleton)

            if self.umask is not None:
                cmd.append('-K')
                cmd.append('UMASK=' + self.umask)

        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg="Group %s does not exist" % self.group)
            ginfo = self.group_info(self.group)
            if info[3] != ginfo[2]:
                cmd.append('-g')
                cmd.append(self.group)

        if self.shell is not None and info[6] != self.shell:
            cmd.append('-s')
            cmd.append(self.shell)

        if self.login_class is not None:
            # find current login class
            user_login_class = None
            if os.path.exists(self.SHADOWFILE) and os.access(self.SHADOWFILE, os.R_OK):
                with open(self.SHADOWFILE, 'r') as f:
                    for line in f:
                        if line.startswith('%s:' % self.name):
                            user_login_class = line.split(':')[4]

            # act only if login_class change
            if self.login_class != user_login_class:
                cmd.append('-L')
                cmd.append(self.login_class)

        if self.groups is not None:
            current_groups = self.user_group_membership()
            groups = self.get_groups_set(names_only=True)

            group_diff = set(current_groups).symmetric_difference(groups)
            groups_need_mod = False

            if group_diff:
                if self.append:
                    for g in groups:
                        if g in group_diff:
                            groups_need_mod = True
                            break
                else:
                    groups_need_mod = True

            if groups_need_mod:
                cmd.append('-G')
                new_groups = groups
                if self.append:
                    new_groups = groups | set(current_groups)
                cmd.append(','.join(new_groups))

        if self.expires is not None:

            current_expires = self.user_password()[1] or '0'
            current_expires = int(current_expires)

            # If expiration is negative or zero and the current expiration is greater than zero, disable expiration.
            # In OpenBSD, setting expiration to zero disables expiration. It does not expire the account.
            if self.expires <= time.gmtime(0):
                if current_expires > 0:
                    cmd.append('-e')
                    cmd.append('0')
            else:
                # Convert days since Epoch to seconds since Epoch as struct_time
                current_expire_date = time.gmtime(current_expires)

                # Current expires is negative or we compare year, month, and day only
                if current_expires <= 0 or current_expire_date[:3] != self.expires[:3]:
                    cmd.append('-e')
                    cmd.append(str(calendar.timegm(self.expires)))

        (rc, out, err) = (None, '', '')

        # modify the user if cmd will do anything
        if cmd_len != len(cmd):
            (rc, _out, _err) = self.execute_command(cmd)
            out += _out
            err += _err

            if rc is not None and rc != 0:
                self.module.fail_json(name=self.name, msg=err, rc=rc)

        # we have to set the password in a second command
        if self.update_password == 'always' and self.password is not None and info[1].lstrip('*LOCKED*') != self.password.lstrip('*LOCKED*'):
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