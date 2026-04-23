def check_service_changed(self):
        if self.state and self.running is None:
            self.module.fail_json(msg="failed determining service state, possible typo of service name?")
        # Find out if state has changed
        if not self.running and self.state in ["reloaded", "started"]:
            self.svc_change = True
        elif self.running and self.state in ["reloaded", "stopped"]:
            self.svc_change = True
        elif self.state == "restarted":
            self.svc_change = True
        if self.module.check_mode and self.svc_change:
            self.module.exit_json(changed=True, msg='service state changed')