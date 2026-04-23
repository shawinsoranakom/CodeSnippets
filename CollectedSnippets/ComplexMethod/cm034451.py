def service_control(self):

        # Check if service name is a subsystem of a group subsystem
        rc, stdout, stderr = self.execute_command("%s -a" % (self.lssrc_cmd))
        if rc == 1:
            if stderr:
                self.module.fail_json(msg=stderr)
            else:
                self.module.fail_json(msg=stdout)
        else:
            lines = stdout.splitlines()
            subsystems = []
            groups = []
            for line in lines[1:]:
                subsystem = line.split()[0].strip()
                group = line.split()[1].strip()
                subsystems.append(subsystem)
                if group:
                    groups.append(group)

            # Define if service name parameter:
            # -s subsystem or -g group subsystem
            if self.name in subsystems:
                srccmd_parameter = "-s"
            elif self.name in groups:
                srccmd_parameter = "-g"

        if self.action == 'start':
            srccmd = self.startsrc_cmd
        elif self.action == 'stop':
            srccmd = self.stopsrc_cmd
        elif self.action == 'reload':
            srccmd = self.refresh_cmd
        elif self.action == 'restart':
            self.execute_command("%s %s %s" % (self.stopsrc_cmd, srccmd_parameter, self.name))
            if self.sleep:
                time.sleep(self.sleep)
            srccmd = self.startsrc_cmd

        if self.arguments and self.action in ('start', 'restart'):
            return self.execute_command("%s -a \"%s\" %s %s" % (srccmd, self.arguments, srccmd_parameter, self.name))
        else:
            return self.execute_command("%s %s %s" % (srccmd, srccmd_parameter, self.name))