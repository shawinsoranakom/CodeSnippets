def get_service_status(self):
        if self.svc_cmd and self.svc_cmd.endswith('systemctl'):
            return self.get_systemd_service_status()

        self.action = "status"
        rc, status_stdout, status_stderr = self.service_control()

        # if we have decided the service is managed by upstart, we check for some additional output...
        if self.svc_initctl and self.running is None:
            # check the job status by upstart response
            initctl_rc, initctl_status_stdout, initctl_status_stderr = self.execute_command("%s status %s %s" % (self.svc_initctl, self.name, self.arguments))
            if "stop/waiting" in initctl_status_stdout:
                self.running = False
            elif "start/running" in initctl_status_stdout:
                self.running = True

        if self.svc_cmd and self.svc_cmd.endswith("rc-service") and self.running is None:
            openrc_rc, openrc_status_stdout, openrc_status_stderr = self.execute_command("%s %s status" % (self.svc_cmd, self.name))
            self.running = "started" in openrc_status_stdout
            self.crashed = "crashed" in openrc_status_stderr

        # Prefer a non-zero return code. For reference, see:
        # http://refspecs.linuxbase.org/LSB_4.1.0/LSB-Core-generic/LSB-Core-generic/iniscrptact.html
        if self.running is None and rc in [1, 2, 3, 4, 69]:
            self.running = False

        # if the job status is still not known check it by status output keywords
        # Only check keywords if there's only one line of output (some init
        # scripts will output verbosely in case of error and those can emit
        # keywords that are picked up as false positives
        if self.running is None and status_stdout.count('\n') <= 1:
            # first transform the status output that could irritate keyword matching
            cleanout = status_stdout.lower().replace(self.name.lower(), '')
            if "stop" in cleanout:
                self.running = False
            elif "run" in cleanout:
                self.running = not ("not " in cleanout)
            elif "start" in cleanout and "not " not in cleanout:
                self.running = True
            elif 'could not access pid file' in cleanout:
                self.running = False
            elif 'is dead and pid file exists' in cleanout:
                self.running = False
            elif 'dead but subsys locked' in cleanout:
                self.running = False
            elif 'dead but pid file exists' in cleanout:
                self.running = False

        # if the job status is still not known and we got a zero for the
        # return code, assume here that the service is running
        if self.running is None and rc == 0:
            self.running = True

        # if the job status is still not known check it by special conditions
        if self.running is None:
            if self.name == 'iptables' and "ACCEPT" in status_stdout:
                # iptables status command output is lame
                # TODO: lookup if we can use a return code for this instead?
                self.running = True

        return self.running