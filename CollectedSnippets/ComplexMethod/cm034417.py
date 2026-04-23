def modify_user(self):
        changed = None
        out = ''
        err = ''

        if self.group:
            self._make_group_numerical()

        for field in self.fields:
            if field[0] in self.__dict__ and self.__dict__[field[0]]:
                current = self._get_user_property(field[1])
                if current is None or current != to_text(self.__dict__[field[0]]):
                    cmd = self._get_dscl()
                    cmd += ['-create', '/Users/%s' % self.name, field[1], self.__dict__[field[0]]]
                    (rc, _out, _err) = self.execute_command(cmd)
                    if rc != 0:
                        self.module.fail_json(
                            msg='Cannot update property "%s" for user "%s".'
                                % (field[0], self.name), err=err, out=out, rc=rc)
                    changed = rc
                    out += _out
                    err += _err
        if self.update_password == 'always' and self.password is not None:
            (rc, _out, _err) = self._change_user_password()
            out += _out
            err += _err
            changed = rc

        if self.groups:
            (rc, _out, _err, _changed) = self._modify_group()
            out += _out
            err += _err

            if _changed is True:
                changed = rc

        rc = self._update_system_user()
        if rc == 0:
            changed = rc

        return (changed, out, err)