def service_enable(self):
        # Get current service enablement status
        rc, stdout, stderr = self.execute_command("%s -l %s" % (self.svcs_cmd, self.name))

        if rc != 0:
            if stderr:
                self.module.fail_json(msg=stderr)
            else:
                self.module.fail_json(msg=stdout)

        enabled = False
        temporary = False

        # look for enabled line, which could be one of:
        #    enabled   true (temporary)
        #    enabled   false (temporary)
        #    enabled   true
        #    enabled   false
        for line in stdout.split("\n"):
            if line.startswith("enabled"):
                if "true" in line:
                    enabled = True
                if "temporary" in line:
                    temporary = True

        startup_enabled = (enabled and not temporary) or (not enabled and temporary)

        if self.enable and startup_enabled:
            return
        elif (not self.enable) and (not startup_enabled):
            return

        if not self.module.check_mode:
            # Mark service as started or stopped (this will have the side effect of
            # actually stopping or starting the service)
            if self.enable:
                subcmd = "enable -rs"
            else:
                subcmd = "disable -s"

            rc, stdout, stderr = self.execute_command("%s %s %s" % (self.svcadm_cmd, subcmd, self.name))

            if rc != 0:
                if stderr:
                    self.module.fail_json(msg=stderr)
                else:
                    self.module.fail_json(msg=stdout)

        self.changed = True