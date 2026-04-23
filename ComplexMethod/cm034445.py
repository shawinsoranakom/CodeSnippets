def service_enable(self):

        if self.enable_cmd is None:
            self.module.fail_json(msg='cannot detect command to enable service %s, typo or init system potentially unknown' % self.name)

        self.changed = True
        action = None

        #
        # Upstart's initctl
        #
        if self.enable_cmd.endswith("initctl"):
            def write_to_override_file(file_name, file_contents, ):
                with open(file_name, 'w') as override_file:
                    override_file.write(file_contents)

            initpath = '/etc/init'
            if self.upstart_version >= LooseVersion('0.6.7'):
                manreg = re.compile(r'^manual\s*$', re.M | re.I)
                config_line = 'manual\n'
            else:
                manreg = re.compile(r'^start on manual\s*$', re.M | re.I)
                config_line = 'start on manual\n'
            conf_file_name = "%s/%s.conf" % (initpath, self.name)
            override_file_name = "%s/%s.override" % (initpath, self.name)

            # Check to see if files contain the manual line in .conf and fail if True
            with open(conf_file_name) as conf_file_fh:
                conf_file_content = conf_file_fh.read()
            if manreg.search(conf_file_content):
                self.module.fail_json(msg="manual stanza not supported in a .conf file")

            self.changed = False
            if os.path.exists(override_file_name):
                with open(override_file_name) as override_fh:
                    override_file_contents = override_fh.read()
                # Remove manual stanza if present and service enabled
                if self.enable and manreg.search(override_file_contents):
                    self.changed = True
                    override_state = manreg.sub('', override_file_contents)
                # Add manual stanza if not present and service disabled
                elif not (self.enable) and not (manreg.search(override_file_contents)):
                    self.changed = True
                    override_state = '\n'.join((override_file_contents, config_line))
                # service already in desired state
                else:
                    pass
            # Add file with manual stanza if service disabled
            elif not (self.enable):
                self.changed = True
                override_state = config_line
            else:
                # service already in desired state
                pass

            if self.module.check_mode:
                self.module.exit_json(changed=self.changed)

            # The initctl method of enabling and disabling services is much
            # different than for the other service methods.  So actually
            # committing the change is done in this conditional and then we
            # skip the boilerplate at the bottom of the method
            if self.changed:
                try:
                    write_to_override_file(override_file_name, override_state)
                except Exception:
                    self.module.fail_json(msg='Could not modify override file')

            return

        #
        # SysV's chkconfig
        #
        if self.enable_cmd.endswith("chkconfig"):
            if self.enable:
                action = 'on'
            else:
                action = 'off'

            (rc, out, err) = self.execute_command("%s --list %s" % (self.enable_cmd, self.name))
            if 'chkconfig --add %s' % self.name in err:
                self.execute_command("%s --add %s" % (self.enable_cmd, self.name))
                (rc, out, err) = self.execute_command("%s --list %s" % (self.enable_cmd, self.name))
            if self.name not in out:
                self.module.fail_json(msg="service %s does not support chkconfig" % self.name)
            # TODO: look back on why this is here
            # state = out.split()[-1]

            # Check if we're already in the correct state
            if "3:%s" % action in out and "5:%s" % action in out:
                self.changed = False
                return

        #
        # Systemd's systemctl
        #
        if self.enable_cmd.endswith("systemctl"):
            if self.enable:
                action = 'enable'
            else:
                action = 'disable'

            # Check if we're already in the correct state
            service_enabled = self.get_systemd_service_enabled()

            # self.changed should already be true
            if self.enable == service_enabled:
                self.changed = False
                return

        #
        # OpenRC's rc-update
        #
        if self.enable_cmd.endswith("rc-update"):
            if self.enable:
                action = 'add'
            else:
                action = 'delete'

            (rc, out, err) = self.execute_command("%s show" % self.enable_cmd)
            for line in out.splitlines():
                service_name, runlevels = line.split('|')
                service_name = service_name.strip()
                if service_name != self.name:
                    continue
                runlevels = re.split(r'\s+', runlevels)
                # service already enabled for the runlevel
                if self.enable and self.runlevel in runlevels:
                    self.changed = False
                # service already disabled for the runlevel
                elif not self.enable and self.runlevel not in runlevels:
                    self.changed = False
                break
            else:
                # service already disabled altogether
                if not self.enable:
                    self.changed = False

            if not self.changed:
                return

        #
        # update-rc.d style
        #
        if self.enable_cmd.endswith("update-rc.d"):

            enabled = False
            slinks = glob.glob('/etc/rc?.d/S??' + self.name)
            if slinks:
                enabled = True

            if self.enable != enabled:
                self.changed = True

                if self.enable:
                    action = 'enable'
                    klinks = glob.glob('/etc/rc?.d/K??' + self.name)
                    if not klinks:
                        if not self.module.check_mode:
                            (rc, out, err) = self.execute_command("%s %s defaults" % (self.enable_cmd, self.name))
                            if rc != 0:
                                if err:
                                    self.module.fail_json(msg=err)
                                else:
                                    self.module.fail_json(msg=out) % (self.enable_cmd, self.name, action)
                else:
                    action = 'disable'

                if not self.module.check_mode:
                    (rc, out, err) = self.execute_command("%s %s %s" % (self.enable_cmd, self.name, action))
                    if rc != 0:
                        if err:
                            self.module.fail_json(msg=err)
                        else:
                            self.module.fail_json(msg=out) % (self.enable_cmd, self.name, action)
            else:
                self.changed = False

            return

        #
        # insserv (Debian <=7, SLES, others)
        #
        if self.enable_cmd.endswith("insserv"):
            if self.enable:
                (rc, out, err) = self.execute_command("%s -n -v %s" % (self.enable_cmd, self.name))
            else:
                (rc, out, err) = self.execute_command("%s -n -r -v %s" % (self.enable_cmd, self.name))

            self.changed = False
            for line in err.splitlines():
                if self.enable and line.find('enable service') != -1:
                    self.changed = True
                    break
                if not self.enable and line.find('remove service') != -1:
                    self.changed = True
                    break

            if self.module.check_mode:
                self.module.exit_json(changed=self.changed)

            if not self.changed:
                return

            if self.enable:
                (rc, out, err) = self.execute_command("%s %s" % (self.enable_cmd, self.name))
                if (rc != 0) or (err != ''):
                    self.module.fail_json(msg=("Failed to install service. rc: %s, out: %s, err: %s" % (rc, out, err)))
                return (rc, out, err)
            else:
                (rc, out, err) = self.execute_command("%s -r %s" % (self.enable_cmd, self.name))
                if (rc != 0) or (err != ''):
                    self.module.fail_json(msg=("Failed to remove service. rc: %s, out: %s, err: %s" % (rc, out, err)))
                return (rc, out, err)

        #
        # If we've gotten to the end, the service needs to be updated
        #
        self.changed = True

        # we change argument order depending on real binary used:
        # rc-update and systemctl need the argument order reversed

        if self.enable_cmd.endswith("rc-update"):
            args = (self.enable_cmd, action, self.name + " " + self.runlevel)
        elif self.enable_cmd.endswith("systemctl"):
            args = (self.enable_cmd, action, self.__systemd_unit)
        else:
            args = (self.enable_cmd, self.name, action)

        if self.module.check_mode:
            self.module.exit_json(changed=self.changed)

        (rc, out, err) = self.execute_command("%s %s %s" % args)
        if rc != 0:
            if err:
                self.module.fail_json(msg="Error when trying to %s %s: rc=%s %s" % (action, self.name, rc, err))
            else:
                self.module.fail_json(msg="Failure for %s %s: rc=%s %s" % (action, self.name, rc, out))

        return (rc, out, err)