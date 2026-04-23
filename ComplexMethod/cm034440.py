def modify_service_state(self):

        # Only do something if state will change
        if self.svc_change:
            # Control service
            if self.state in ['started']:
                self.action = "start"
            elif not self.running and self.state == 'reloaded':
                self.action = "start"
            elif self.state == 'stopped':
                self.action = "stop"
            elif self.state == 'reloaded':
                self.action = "reload"
            elif self.state == 'restarted':
                self.action = "restart"

            if self.module.check_mode:
                self.module.exit_json(changed=True, msg='changing service state')

            return self.service_control()

        else:
            # If nothing needs to change just say all is well
            rc = 0
            err = ''
            out = ''
            return rc, out, err