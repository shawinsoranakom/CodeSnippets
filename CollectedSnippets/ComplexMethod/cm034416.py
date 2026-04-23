def create_user(self, command_name='dscl'):
        cmd = self._get_dscl()
        cmd += ['-create', '/Users/%s' % self.name]
        (rc, out, err) = self.execute_command(cmd)
        if rc != 0:
            self.module.fail_json(msg='Cannot create user "%s".' % self.name, err=err, out=out, rc=rc)

        # Make the Gecos (alias display name) default to username
        if self.comment is None:
            self.comment = self.name

        # Make user group default to 'staff'
        if self.group is None:
            self.group = 'staff'

        self._make_group_numerical()
        if self.uid is None:
            self.uid = str(self._get_next_uid(self.system))

        # Homedir is not created by default
        if self.create_home:
            if self.home is None:
                self.home = '/Users/%s' % self.name
            if not self.module.check_mode:
                if not os.path.exists(self.home):
                    os.makedirs(self.home)
                self.chown_homedir(int(self.uid), int(self.group), self.home)

        # dscl sets shell to /usr/bin/false when UserShell is not specified
        # so set the shell to /bin/bash when the user is not a system user
        if not self.system and self.shell is None:
            self.shell = '/bin/bash'

        for field in self.fields:
            if field[0] in self.__dict__ and self.__dict__[field[0]]:

                cmd = self._get_dscl()
                cmd += ['-create', '/Users/%s' % self.name, field[1], self.__dict__[field[0]]]
                (rc, _out, _err) = self.execute_command(cmd)
                if rc != 0:
                    self.module.fail_json(msg='Cannot add property "%s" to user "%s".' % (field[0], self.name), err=err, out=out, rc=rc)

                out += _out
                err += _err
                if rc != 0:
                    return (rc, _out, _err)

        (rc, _out, _err) = self._change_user_password()
        out += _out
        err += _err

        self._update_system_user()
        # here we don't care about change status since it is a creation,
        # thus changed is always true.
        if self.groups:
            (rc, _out, _err, changed) = self._modify_group()
            out += _out
            err += _err
        return (rc, out, err)