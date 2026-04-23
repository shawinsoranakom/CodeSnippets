def service_enable(self):
        if self.enable:
            self.rcconf_value = "YES"
        else:
            self.rcconf_value = "NO"

        rcfiles = ['/etc/rc.conf', '/etc/rc.conf.local', '/usr/local/etc/rc.conf']
        for rcfile in rcfiles:
            if os.path.isfile(rcfile):
                self.rcconf_file = rcfile

        rc, stdout, stderr = self.execute_command("%s %s %s %s" % (self.svc_cmd, self.arguments, self.name, 'rcvar'))
        try:
            rcvars = shlex.split(stdout, comments=True)
        except Exception:
            # TODO: add a warning to the output with the failure
            pass

        if not rcvars:
            self.module.fail_json(msg="unable to determine rcvar", stdout=stdout, stderr=stderr)

        # In rare cases, i.e. sendmail, rcvar can return several key=value pairs
        # Usually there is just one, however.  In other rare cases, i.e. uwsgi,
        # rcvar can return extra uncommented data that is not at all related to
        # the rcvar.  We will just take the first key=value pair we come across
        # and hope for the best.
        for rcvar in rcvars:
            if '=' in rcvar:
                self.rcconf_key, default_rcconf_value = rcvar.split('=', 1)
                break

        if self.rcconf_key is None:
            self.module.fail_json(msg="unable to determine rcvar", stdout=stdout, stderr=stderr)

        if self.sysrc_cmd:  # FreeBSD >= 9.2

            rc, current_rcconf_value, stderr = self.execute_command("%s -n %s" % (self.sysrc_cmd, self.rcconf_key))
            # it can happen that rcvar is not set (case of a system coming from the ports collection)
            # so we will fallback on the default
            if rc != 0:
                current_rcconf_value = default_rcconf_value

            if current_rcconf_value.strip().upper() != self.rcconf_value:

                self.changed = True

                if self.module.check_mode:
                    self.module.exit_json(changed=True, msg="changing service enablement")

                rc, change_stdout, change_stderr = self.execute_command("%s %s=\"%s\"" % (self.sysrc_cmd, self.rcconf_key, self.rcconf_value))
                if rc != 0:
                    self.module.fail_json(msg="unable to set rcvar using sysrc", stdout=change_stdout, stderr=change_stderr)

                # sysrc does not exit with code 1 on permission error => validate successful change using service(8)
                rc, check_stdout, check_stderr = self.execute_command("%s %s %s" % (self.svc_cmd, self.name, "enabled"))
                if self.enable != (rc == 0):  # rc = 0 indicates enabled service, rc = 1 indicates disabled service
                    self.module.fail_json(msg="unable to set rcvar: sysrc did not change value", stdout=change_stdout, stderr=change_stderr)

            else:
                self.changed = False

        else:  # Legacy (FreeBSD < 9.2)
            try:
                return self.service_enable_rcconf()
            except Exception:
                self.module.fail_json(msg='unable to set rcvar')