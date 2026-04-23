def service_control(self):

        # Decide what command to run
        svc_cmd = ''
        arguments = self.arguments
        if self.svc_cmd:
            if not self.svc_cmd.endswith("systemctl"):
                if self.svc_cmd.endswith("initctl"):
                    # initctl commands take the form <cmd> <action> <name>
                    svc_cmd = self.svc_cmd
                    arguments = "%s %s" % (self.name, arguments)
                else:
                    # SysV and OpenRC take the form <cmd> <name> <action>
                    svc_cmd = "%s %s" % (self.svc_cmd, self.name)
            else:
                # systemd commands take the form <cmd> <action> <name>
                svc_cmd = self.svc_cmd
                arguments = "%s %s" % (self.__systemd_unit, arguments)
        elif self.svc_cmd is None and self.svc_initscript:
            # upstart
            svc_cmd = "%s" % self.svc_initscript

        # In OpenRC, if a service crashed, we need to reset its status to
        # stopped with the zap command, before we can start it back.
        if self.svc_cmd and self.svc_cmd.endswith('rc-service') and self.action == 'start' and self.crashed:
            self.execute_command("%s zap" % svc_cmd, daemonize=True)

        if self.action != "restart":
            if svc_cmd != '':
                # upstart or systemd or OpenRC
                rc_state, stdout, stderr = self.execute_command("%s %s %s" % (svc_cmd, self.action, arguments), daemonize=True)
            else:
                # SysV
                rc_state, stdout, stderr = self.execute_command("%s %s %s" % (self.action, self.name, arguments), daemonize=True)
        elif self.svc_cmd and self.svc_cmd.endswith('rc-service'):
            # All services in OpenRC support restart.
            rc_state, stdout, stderr = self.execute_command("%s %s %s" % (svc_cmd, self.action, arguments), daemonize=True)
        else:
            # In other systems, not all services support restart. Do it the hard way.
            if svc_cmd != '':
                # upstart or systemd
                rc1, stdout1, stderr1 = self.execute_command("%s %s %s" % (svc_cmd, 'stop', arguments), daemonize=True)
            else:
                # SysV
                rc1, stdout1, stderr1 = self.execute_command("%s %s %s" % ('stop', self.name, arguments), daemonize=True)

            if self.sleep:
                time.sleep(self.sleep)

            if svc_cmd != '':
                # upstart or systemd
                rc2, stdout2, stderr2 = self.execute_command("%s %s %s" % (svc_cmd, 'start', arguments), daemonize=True)
            else:
                # SysV
                rc2, stdout2, stderr2 = self.execute_command("%s %s %s" % ('start', self.name, arguments), daemonize=True)

            # merge return information
            if rc1 != 0 and rc2 == 0:
                rc_state = rc2
                stdout = stdout2
                stderr = stderr2
            else:
                rc_state = rc1 + rc2
                stdout = stdout1 + stdout2
                stderr = stderr1 + stderr2

        return (rc_state, stdout, stderr)