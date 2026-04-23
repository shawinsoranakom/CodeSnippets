def service_enable(self):

        if not self.enable_cmd:
            return super(OpenBsdService, self).service_enable()

        rc, stdout, stderr = self.execute_command("%s %s %s %s" % (self.enable_cmd, 'get', self.name, 'status'))

        status_action = None
        if self.enable:
            if rc != 0:
                status_action = "on"
        elif self.enable is not None:
            # should be explicit False at this point
            if rc != 1:
                status_action = "off"

        if status_action is not None:
            self.changed = True
            if not self.module.check_mode:
                rc, stdout, stderr = self.execute_command("%s set %s status %s" % (self.enable_cmd, self.name, status_action))

                if rc != 0:
                    if stderr:
                        self.module.fail_json(msg=stderr)
                    else:
                        self.module.fail_json(msg="rcctl failed to modify service status")