def modify_user(self):
        current_groups = self.user_group_membership()
        groups = []
        rc = None
        out = ''
        err = ''
        user_info = self.user_info()

        if not user_info:
            return rc, out, err

        gid = user_info[3]
        if self.group is not None:
            if not self.group_exists(self.group):
                self.module.fail_json(msg=f'Group {self.group} does not exist')

            group_info = self.group_info(self.group)
            if group_info:
                gid = group_info[2]

        add_cmd_bin = self.module.get_bin_path('adduser', True)
        remove_cmd_bin = self.module.get_bin_path('delgroup', True)

        # Manage group membership
        if self.groups:
            groups = self.get_groups_set() or set()
            group_diff = set(current_groups).symmetric_difference(groups)

            if group_diff:
                for g in groups:
                    if g in group_diff:
                        add_cmd = [add_cmd_bin, self.name, g]
                        rc, out, err = self.execute_command(add_cmd)
                        if rc is not None and rc != 0:
                            self.module.fail_json(name=self.name, msg=err, rc=rc)

                for g in group_diff:
                    if g not in groups and not self.append:
                        remove_cmd = [remove_cmd_bin, self.name, g]
                        rc, out, err = self.execute_command(remove_cmd)
                        if rc is not None and rc != 0:
                            self.module.fail_json(name=self.name, msg=err, rc=rc)

        # Manage password
        current_password = to_native(user_info[1])
        new_password = self._build_password_string(current_password)
        if self.update_password == 'always':
            lock_status_mismatch = self.password_lock and not current_password.startswith('!')
            password_changed = new_password != current_password
            if lock_status_mismatch or password_changed:
                cmd = [self.module.get_bin_path('chpasswd', True), '--encrypted']
                data = f'{self.name}:{new_password}'
                rc, out, err = self.execute_command(cmd, data=data)

                if rc is not None and rc != 0:
                    self.module.fail_json(name=self.name, msg=err, rc=rc)

        # Manage user settings
        uid = user_info[2]
        if self.uid is not None:
            uid = self.uid

        passwd_entry = [
            self.name,
            'x',
            to_native(uid),
            to_native(gid),
            self.comment or user_info[4],
            self.home or user_info[5],
            self.shell or user_info[6],
        ]

        contents = []
        change = False
        with open(self.PASSWORDFILE, 'r') as password_file:
            for line in password_file:
                if line.startswith('%s:' % self.name):
                    fields = line.strip().split(':')
                    if fields != passwd_entry:
                        change = True
                        line = ':'.join(passwd_entry) + '\n'

                contents.append(line)

        if change:
            rc = 0
            if not self.module.check_mode:
                tmpfd, tmpfile = tempfile.mkstemp(dir=self.module.tmpdir)
                with os.fdopen(tmpfd, 'w') as f:
                    f.writelines(contents)

                self.module.backup_local(self.PASSWORDFILE)
                self.module.atomic_move(tmpfile, self.PASSWORDFILE)

        # Manage home directory
        if self.move_home:
            usermod_bin = self.module.get_bin_path('usermod')
            if usermod_bin is not None:
                cmd = [usermod_bin, '-d', self.home, '-m', self.name]
                rc, out, err = self.execute_command(cmd)
                if rc is not None and rc != 0:
                    self.module.fail_json(name=self.name, msg=err, rc=rc)
            else:
                self.module.warn("usermod command not found, skipping home directory move")
        return rc, out, err