def service_control(self):
        status = self.get_sunos_svcs_status()

        # if starting or reloading, clear maintenance states
        if self.action in ['start', 'reload', 'restart'] and status in ['maintenance', 'degraded']:
            rc, stdout, stderr = self.execute_command("%s clear %s" % (self.svcadm_cmd, self.name))
            if rc != 0:
                return rc, stdout, stderr
            status = self.get_sunos_svcs_status()

        if status in ['maintenance', 'degraded']:
            self.module.fail_json(msg="Failed to bring service out of %s status." % status)

        if self.action == 'start':
            subcmd = "enable -rst"
        elif self.action == 'stop':
            subcmd = "disable -st"
        elif self.action == 'reload':
            subcmd = "refresh %s" % (self.svcadm_sync)
        elif self.action == 'restart' and status == 'online':
            subcmd = "restart %s" % (self.svcadm_sync)
        elif self.action == 'restart' and status != 'online':
            subcmd = "enable -rst"

        return self.execute_command("%s %s %s" % (self.svcadm_cmd, subcmd, self.name))